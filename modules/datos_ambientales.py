"""Procesamiento ambiental (RF-07, RF-08, RF-15): consulta las fuentes, guarda los datos en la tabla
Datos_Ambientales y los convierte en el clima y el suelo que usa el motor."""
import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import delete, select

from config import FUENTE_RESPALDO, RESPALDO_NASA, VIGENCIA_DATOS_DIAS
from database.conexion import sesion
from database.modelos import DatoAmbiental, Parcela
from modules import lenguaje_sencillo
from services import ServicioNoDisponible, gpm, nasa_power, ndvi, smap, soilgrids, srtm
from utils.calculos import MESES_L, clima_estimado, completar_clima, distancia_km, textura_usda
from utils.validaciones import TEXTURAS

RAIZ = Path(__file__).resolve().parent.parent
CANTONES = json.loads((RAIZ / "data" / "cantones.json").read_text(encoding="utf-8"))["cantones"]
RESPALDO_SUELO = RAIZ / "data" / "soilgrids_cantones.json"
FUENTE_RESPALDO_SUELO = "SoilGrids (referencia cantonal)"
VIGENCIA_DIAS = VIGENCIA_DATOS_DIAS
GRADIENTE = -0.0058  # °C por metro

# Funciones de consulta (se pueden reemplazar en las pruebas)
SERVICIOS = {
    "NASA POWER": nasa_power.consultar,
    "NASA SRTM": srtm.consultar,
    "SoilGrids": soilgrids.consultar,
    "NASA NDVI": ndvi.consultar,
    "NASA GPM": gpm.consultar,
    "NASA SMAP": smap.consultar,
}

# Tabla de fusión y armonización multiescala para Vista Técnica y Acerca
TABLA_FUSION_ESCALAS = [
    {
        "Fuente satelital": "NASA SRTM",
        "Resolución": "30 m",
        "Variables": "Altitud (m) y pendiente (%)",
        "Armonización al polígono": "Muestreo en cruz de 5 puntos (paso 60 m) en torno al centroide del lote.",
        "Incertidumbre espacial": "Baja en laderas amplias; moderada en terrazas menores a 30 m.",
    },
    {
        "Fuente satelital": "SoilGrids (ISRIC)",
        "Resolución": "250 m",
        "Variables": "pH, materia orgánica, arena, arcilla y textura USDA",
        "Armonización al polígono": "Media ponderada 0–30 cm en el punto; sustituida por datos del agricultor o laboratorio.",
        "Incertidumbre espacial": "Media-Alta (variabilidad intraparcela requiere muestreo en campo).",
    },
    {
        "Fuente satelital": "MODIS / Landsat / Sentinel-2 NDVI",
        "Resolución": "30–250 m",
        "Variables": "Índice NDVI mensual (0,15–0,85) y suelo desnudo",
        "Armonización al polígono": "Serie estacional calibrada para Chimborazo y modulada por altitud y lluvia local.",
        "Incertidumbre espacial": "Baja-Media (Landsat/Sentinel 10–30 m cubren parcelas ≥ 0,25 ha; MODIS 250 m mezcla bordes).",
    },
    {
        "Fuente satelital": "NASA GPM IMERG",
        "Resolución": "~10 km",
        "Variables": "Frecuencia de lluvias intensas e intensidad máxima (mm/día)",
        "Armonización al polígono": "Cruce con la pendiente SRTM (30 m) para estimar lavado e índice de erosividad.",
        "Incertidumbre espacial": "Media (tormentas convectivas andinas pueden variar dentro de la celda de 10 km).",
    },
    {
        "Fuente satelital": "NASA SMAP L3/L4",
        "Resolución": "9–36 km",
        "Variables": "Humedad superficial, radicular y anomalía hídrica (%)",
        "Armonización al polígono": "Ajuste inicial del balance hídrico mensual y conexión con escenarios del simulador.",
        "Incertidumbre espacial": "Alta a escala de lote (se contrasta con riego y drenaje reportados en parcela).",
    },
    {
        "Fuente satelital": "NASA POWER (MERRA-2)",
        "Resolución": "~50 km",
        "Variables": "Lluvia, T2M, T2M_MIN, T2M_MAX, radiación solar y GWETROOT",
        "Armonización al polígono": "Downscaling térmico (-0,58 °C/100 m vía SRTM) y calibración con pluviometría cantonal.",
        "Incertidumbre espacial": "Alta en lluvia orográfica de montaña; reducida mediante calibración cantonal.",
    },
]


# ------------------------------------------------------------------ almacenamiento
def _a_filas(fuente: str, d: dict) -> list[tuple]:
    if fuente == "NASA POWER":
        filas = [("ELEV_CELDA", d["elev_celda"], "m")] if d.get("elev_celda") is not None else []
        for i, m in enumerate(d["meses"], 1):
            filas += [(f"P_{i:02d}", m["p"], "mm"), (f"T_{i:02d}", m["t"], "°C"),
                      (f"TMIN_{i:02d}", m["tmin"], "°C"), (f"TMAX_{i:02d}", m["tmax"], "°C")]
            if m.get("rad") is not None:
                filas.append((f"RAD_{i:02d}", m["rad"], "kWh/m2/d"))
            if m.get("gwetroot") is not None:
                filas.append((f"GWR_{i:02d}", m["gwetroot"], "0-1"))
        return filas
    if fuente == "NASA SRTM":
        return [("ELEVACION", d["elevacion"], "m"), ("PENDIENTE", d["pendiente"], "%")]
    if fuente == "NASA NDVI":
        filas = [("NDVI_PROM", d["ndvi_promedio"], "0-1"), ("NDVI_ACT", d["ndvi_actual"], "0-1")]
        filas += [(f"NDVI_{i:02d}", v, "0-1") for i, v in enumerate(d["curva_estacional"], 1)]
        return filas
    if fuente == "NASA GPM":
        filas = [("GPM_INT_MAX", d["intensidad_max_mm_dia"], "mm/d")]
        filas += [(f"GPM_{i:02d}", v, "d/mes") for i, v in enumerate(d["frecuencia_mensual_intensa"], 1)]
        return filas
    if fuente == "NASA SMAP":
        filas = [("SMAP_NORM", d["humedad_normal"], "0-1")]
        filas += [(f"SMAP_{i:02d}", v, "0-1") for i, v in enumerate(d["humedad_mensual"], 1)]
        return filas
    return [(v, d[k], u) for v, k, u in (("PH", "ph", "pH"), ("MO", "materia_organica", "%"),
                                          ("ARENA", "arena", "%"), ("ARCILLA", "arcilla", "%"),
                                          ("DIST_M", "distancia_m", "m")) if d.get(k) is not None]


def _de_filas(fuente: str, f: dict) -> dict:
    if fuente == "NASA POWER":
        return {"fuente": fuente, "elev_celda": f.get("ELEV_CELDA"),
                "meses": [{"p": f[f"P_{i:02d}"], "t": f[f"T_{i:02d}"], "tmin": f[f"TMIN_{i:02d}"], "tmax": f[f"TMAX_{i:02d}"],
                           "rad": f.get(f"RAD_{i:02d}"), "gwetroot": f.get(f"GWR_{i:02d}")} for i in range(1, 13)]}
    if fuente == "NASA SRTM":
        pend = f["PENDIENTE"]
        return {"fuente": fuente, "elevacion": f["ELEVACION"], "pendiente": pend, **srtm.evaluar_erosion_ladera(pend)}
    if fuente == "NASA NDVI":
        curva = [f[f"NDVI_{i:02d}"] for i in range(1, 13)]
        return ndvi.reconstruir_desde_curva(
            curva, ndvi_actual=f.get("NDVI_ACT"), fuente="NASA MODIS / Landsat / Sentinel-2 (climatología Chimborazo)"
        )
    if fuente == "NASA GPM":
        freq = [f[f"GPM_{i:02d}"] for i in range(1, 13)]
        return gpm.evaluar_lavado(freq, f["GPM_INT_MAX"])
    if fuente == "NASA SMAP":
        serie = [f[f"SMAP_{i:02d}"] for i in range(1, 13)]
        return smap.reconstruir_desde_curva(serie, humedad_normal=f.get("SMAP_NORM"))
    return {"fuente": fuente, "ph": f.get("PH"), "materia_organica": f.get("MO"), "arena": f.get("ARENA"), "arcilla": f.get("ARCILLA"),
            "textura": textura_usda(f["ARENA"], f["ARCILLA"]) if "ARENA" in f and "ARCILLA" in f else None,
            "distancia_m": f.get("DIST_M")}


def _leer(id_parcela: int, fuente: str) -> tuple[dict | None, date | None]:
    with sesion() as s:
        filas = list(s.scalars(select(DatoAmbiental).where(DatoAmbiental.id_parcela == id_parcela, DatoAmbiental.fuente == fuente)))
    if not filas:
        return None, None
    try:
        return _de_filas(fuente, {r.variable: r.valor for r in filas}), max(r.fecha_dato for r in filas)
    except KeyError:
        return None, None


def _guardar(id_parcela: int, fuente: str, datos: dict) -> None:
    with sesion() as s:
        s.execute(delete(DatoAmbiental).where(DatoAmbiental.id_parcela == id_parcela, DatoAmbiental.fuente == fuente))
        for var, val, uni in _a_filas(fuente, datos):
            s.add(DatoAmbiental(id_parcela=id_parcela, fuente=fuente, variable=var, valor=float(val), unidad=uni))


def obtener(parcela: Parcela, forzar: bool = False) -> dict:
    """Devuelve los datos de cada fuente (o None) y los avisos de fuentes que fallaron (RF-15)."""
    res = {"avisos": [], "fechas": {}}
    for fuente, consultar in SERVICIOS.items():
        datos, fecha = (None, None) if forzar else _leer(parcela.id_parcela, fuente)
        if datos is None or fecha < date.today() - timedelta(days=VIGENCIA_DIAS):
            try:
                datos = consultar(parcela.latitud, parcela.longitud)
                _guardar(parcela.id_parcela, fuente, datos)
                fecha = date.today()
            except ServicioNoDisponible as e:
                if datos is not None:
                    res["avisos"].append(f"{e}. Se usan los datos guardados del {fecha:%d/%m/%Y}.")
                elif fuente == "NASA POWER" and RESPALDO_NASA.exists():
                    datos = json.loads(RESPALDO_NASA.read_text(encoding="utf-8")) | {"fuente": FUENTE_RESPALDO}
                    _guardar(parcela.id_parcela, fuente, datos)
                    fecha = date.today()
                    res["avisos"].append(f"{e}. Se usa el respaldo de NASA POWER de Riobamba (datos reales guardados).")
                elif fuente == "SoilGrids" and (ref := suelo_referencia(parcela.latitud, parcela.longitud)):
                    datos = ref
                    _guardar(parcela.id_parcela, fuente, datos)
                    fecha = date.today()
                    res["avisos"].append(f"SoilGrids tardó en responder. Se guardó el suelo de referencia cantonal de {ref['canton']} (datos reales).")
                else:
                    res["avisos"].append(str(e))
        res[fuente] = datos
        res["fechas"][fuente] = fecha
    return res


# ------------------------------------------------------------------ interpretación
def canton_cercano(lat: float, lon: float) -> dict:
    return min(CANTONES, key=lambda c: distancia_km(lat, lon, c["lat"], c["lon"]))


def suelo_referencia(lat: float, lon: float) -> dict | None:
    """Suelo SoilGrids guardado del cantón más cercano (respaldo si SoilGrids no responde o no tiene la celda)."""
    try:
        refs = json.loads(RESPALDO_SUELO.read_text(encoding="utf-8"))["cantones"]
    except (OSError, ValueError, KeyError):
        return None
    if not refs:
        return None
    r = min(refs, key=lambda c: distancia_km(lat, lon, c["lat"], c["lon"]))
    return {"fuente": FUENTE_RESPALDO_SUELO, "canton": r["nombre"], "ph": r["ph"], "materia_organica": r["materia_organica"],
            "arena": r["arena"], "arcilla": r["arcilla"], "textura": r["textura"]}


def clima_parcela(parcela: Parcela, amb: dict, modo_lluvia: str = "auto") -> dict:
    """Clima mensual corregido para la parcela.
    - Temperatura de NASA POWER corregida por la diferencia de altitud celda-parcela (-0,58 °C/100 m).
    - Lluvia: NASA POWER, o calibrada con la referencia local si difieren mucho (celdas de ~50 km en los Andes)."""
    ref = canton_cercano(parcela.latitud, parcela.longitud)
    dist = distancia_km(parcela.latitud, parcela.longitud, ref["lat"], ref["lon"])
    if amb.get("NASA SRTM"):
        alt, f_alt = amb["NASA SRTM"]["elevacion"], "NASA SRTM"
    else:
        alt, f_alt = ref["altitud"], f"referencia de {ref['nombre']}"
    out = {"altitud": alt, "fuente_altitud": f_alt, "canton": ref["nombre"], "dist_canton_km": dist, "lluvia_ref": ref["lluvia_anual_mm"]}
    power = amb.get("NASA POWER")
    if power:
        dT = GRADIENTE * (alt - power["elev_celda"]) if power.get("elev_celda") is not None else 0
        p_nasa = sum(m["p"] for m in power["meses"]) or 1
        disc = abs(p_nasa - ref["lluvia_anual_mm"]) / ref["lluvia_anual_mm"]
        modo = ("mixta" if disc > 0.4 else "nasa") if modo_lluvia == "auto" else modo_lluvia
        f = {"nasa": 1, "mixta": (1 + ref["lluvia_anual_mm"] / p_nasa) / 2, "local": ref["lluvia_anual_mm"] / p_nasa}[modo]
        meses = [{"p": m["p"] * f, "t": m["t"] + dT, "tmin": m["tmin"] + dT, "tmax": m["tmax"] + dT} for m in power["meses"]]
        out |= {"fuente": power.get("fuente", "NASA POWER"), "meses_crudos": power["meses"], "elev_celda": power.get("elev_celda"), "correccion_t": dT,
                "lluvia_nasa": p_nasa, "discrepancia_lluvia": disc, "modo_lluvia": modo}
    else:
        meses = clima_estimado(alt, ref["lluvia_anual_mm"])
        out |= {"fuente": "Estimación de referencia", "lluvia_nasa": None, "discrepancia_lluvia": None, "modo_lluvia": "local", "correccion_t": 0}
    out["meses_base"] = meses
    out["meses"] = completar_clima(meses)
    out["lluvia_anual"] = sum(m["p"] for m in out["meses"])

    # Vincular NDVI, GPM (con pendiente real de parcela o SRTM) y SMAP
    out["ndvi"] = amb.get("NASA NDVI")
    gpm_raw = amb.get("NASA GPM")
    pend_eff = parcela.pendiente if parcela.pendiente is not None else (amb.get("NASA SRTM") or {}).get("pendiente", 8.0)
    if gpm_raw:
        out["gpm"] = gpm.evaluar_lavado(
            gpm_raw["frecuencia_mensual_intensa"],
            gpm_raw["intensidad_max_mm_dia"],
            pendiente=pend_eff,
            fuente=gpm_raw.get("fuente", "NASA GPM IMERG (climatología Chimborazo)"),
        )
    else:
        out["gpm"] = None
    out["smap"] = amb.get("NASA SMAP")
    return out


def suelo_parcela(parcela: Parcela, amb: dict) -> dict:
    """Combina lo que dijo el agricultor (prioridad), SoilGrids y SRTM. Indica la fuente de cada dato."""
    sg, tr = amb.get("SoilGrids") or {}, amb.get("NASA SRTM") or {}

    def elegir(propio, satelite, fuente_sat, defecto):
        if propio is not None:
            return propio, "agricultor"
        if satelite is not None:
            return satelite, fuente_sat
        return defecto, "supuesto"

    ph, f_ph = elegir(parcela.ph, sg.get("ph"), "SoilGrids", 6.5)
    mo, f_mo = elegir(parcela.materia_organica, sg.get("materia_organica"), "SoilGrids", 2.5)
    tex, f_tex = elegir(parcela.textura, sg.get("textura"), "SoilGrids", "franco")
    pend, f_pend = elegir(parcela.pendiente, tr.get("pendiente"), "NASA SRTM", 8.0)
    ladera = srtm.evaluar_erosion_ladera(pend)
    return {
        "ph": ph,
        "materia_organica": mo,
        "textura": tex,
        "pendiente": pend,
        **ladera,
        "fuentes": {"ph": f_ph, "materia_organica": f_mo, "textura": f_tex, "pendiente": f_pend},
    }


def _rangos(meses: list[int]) -> str:
    return ", ".join(MESES_L[m] for m in meses) if meses else "ninguno"


def diagnostico(parcela: Parcela, clima: dict, suelo: dict, historial: list[dict], sencillo: bool = False) -> list[dict]:
    """Diagnóstico de la parcela (sección 9.2). sencillo=True: sin términos técnicos, para el agricultor."""
    ms = clima["meses"]
    lluviosos = [i for i, m in enumerate(ms) if m["pe"] >= 0.7 * m["et0"]]
    secos = [i for i, m in enumerate(ms) if m["p"] < 0.35 * m["et0"]]
    helada = [i for i, m in enumerate(ms) if m["fr"] > 0.25]
    tmed = sum(m["t"] for m in ms) / 12
    gpm_data = clima.get("gpm")
    smap_data = clima.get("smap")
    ndvi_data = clima.get("ndvi")

    txt_lluvia = (
        f"Llueve unos {clima['lluvia_anual']:,.0f} mm al año. ".replace(",", ".")
        + (f"Los meses con más lluvia son {_rangos(lluviosos)}. " if lluviosos else "Ningún mes tiene lluvia suficiente por sí sola para un cultivo. ")
        + (f"Meses secos: {_rangos(secos)}." if secos else "")
    )
    if gpm_data:
        if sencillo and gpm_data["riesgo_lavado"] == "alto":
            txt_lluvia += " En los meses más lluviosos caen aguaceros fuertes que pueden lavar la tierra."
        elif not sencillo:
            txt_lluvia += f" GPM IMERG: ~{gpm_data['dias_lluvia_intensa_anual']:.0f} días/año de lluvia intensa (riesgo de lavado {gpm_data['riesgo_lavado']})."

    d = [
        {"icono": "🌧️", "titulo": "Lluvias", "texto": txt_lluvia},
        {"icono": "🌡️", "titulo": "Temperatura",
         "texto": f"Clima {'frío' if tmed < 10 else 'fresco' if tmed < 15 else 'templado'} ({tmed:.0f} °C en promedio). "
                  + (f"Hay riesgo de heladas en {_rangos(helada)}." if helada else "El riesgo de heladas es bajo.")},
    ]

    agua = {
        "completo": "Tienes riego siempre: puedes sembrar en cualquier época.",
        "turnos": "Tienes riego por turnos: conviene sembrar con las lluvias y usar el riego como apoyo.",
        "secano": "Solo cuentas con la lluvia: la fecha de siembra es clave.",
    }[parcela.disponibilidad_agua]
    if smap_data:
        if sencillo:
            if smap_data["estado_hidrico"] == "deficit":
                agua += " La tierra viene más seca de lo normal en esta época."
        else:
            agua += (
                f" Humedad superficial SMAP: {smap_data['humedad_superficial_pct']:.0f} % "
                f"(anomalía {smap_data['anomalia_hidrica_pct']:+.1f} %, estado {smap_data['estado_hidrico']})."
            )
    d.append({"icono": "💧", "titulo": "Agua", "texto": agua})

    p = suelo["pendiente"]
    riesgo_lad = suelo.get("riesgo_erosion_ladera", "moderado")
    txt_terreno = f"Altura de {clima['altitud']:,.0f} m. ".replace(",", ".") + (
        "Terreno plano." if p < 5 else f"Pendiente suave ({p:.0f} %)." if p < 12 else f"Pendiente fuerte ({p:.0f} %): hay riesgo de que la lluvia se lleve la tierra."
    )
    if not sencillo:
        txt_terreno += f" Riesgo de erosión en ladera: {riesgo_lad.replace('_', ' ')} (LS {suelo.get('factor_ls', 1.0)})."
    d.append({"icono": "⛰️", "titulo": "Terreno", "texto": txt_terreno})

    # Tarjeta de cobertura vegetal / suelo desnudo (NDVI)
    if sencillo:
        d.append({"icono": "🌿", "titulo": "Cobertura de la tierra", "texto": lenguaje_sencillo.traducir_ndvi(ndvi_data)})
    else:
        if ndvi_data:
            meses_crit = ", ".join(ndvi_data["meses_criticos_nombres"]) or "ninguno"
            txt_ndvi = (
                f"NDVI promedio {ndvi_data['ndvi_promedio']:.2f} (actual {ndvi_data['ndvi_actual']:.2f}; rango estacional "
                f"{ndvi_data['ndvi_min']:.2f}–{ndvi_data['ndvi_max']:.2f}). Meses críticos de suelo desnudo (≤ 0,30): {meses_crit}. "
                f"Riesgo de erosión: {ndvi_data['riesgo_erosion_ndvi']}."
            )
        else:
            txt_ndvi = "Sin serie NDVI disponible para esta parcela."
        d.append({"icono": "🌿", "titulo": "Vegetación y suelo desnudo (NDVI)", "texto": txt_ndvi})

    tex = TEXTURAS.get(suelo["textura"], suelo["textura"]).lower()
    ph = suelo["ph"]
    if sencillo:
        tierra = {
            "arenoso": "suelta y arenosa", "francoarenoso": "suelta", "franco": "negra y suave",
            "francoarcilloso": "algo pesada", "arcilloso": "pesada y barrosa",
        }.get(suelo["textura"], "de tipo medio")
        texto = f"Tu tierra es {tierra}. " + (
            "Es ácida: algunas siembras necesitarán cal. " if ph < 5.5 else
            "Es salitrosa: conviene ponerle abono orgánico. " if ph > 7.5 else ""
        )
        texto += ("Tiene buena cantidad de abono natural (tierra negra)." if suelo["materia_organica"] >= 3
                  else "Le falta abono natural: deja los rastrojos en el terreno y usa estiércol.")
        if getattr(parcela, "drenaje", None) == "empoza":
            texto += " Se empoza el agua: evita sembrar papa, chocho o quinua en la parte baja."
        d.append({"icono": "🟫", "titulo": "Tu tierra", "texto": texto})
    else:
        d.append({
            "icono": "🟫", "titulo": "Suelo",
            "texto": f"Suelo {tex}, pH {ph:.1f} " + (
                "(ácido: algunas leguminosas necesitarán cal)." if ph < 5.5 else
                "(alcalino)." if ph > 7.5 else "(adecuado para la mayoría de cultivos)."
            ) + (" Tiene buena materia orgánica." if suelo["materia_organica"] >= 3 else " Tiene poca materia orgánica."),
        })

    if historial:
        ult = historial[-1]["cultivo"]
        d.append({"icono": "📜", "titulo": "Historial",
                  "texto": f"Último cultivo: {ult['emoji']} {ult['nombre']}. Registraste {len(historial)} siembra(s) en esta parcela."})
    else:
        d.append({"icono": "📜", "titulo": "Historial",
                  "texto": "Aún no registras cultivos anteriores. Agrégalos para mejorar la recomendación."})
    return d
