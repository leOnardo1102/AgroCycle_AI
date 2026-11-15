"""Generación, explicación, escenario testigo y almacenamiento de alternativas de rotación (RF-09 a RF-13, RF-16, sección 13.5)."""
import json
from dataclasses import dataclass, field

from sqlalchemy import select

from database.conexion import sesion
from database.modelos import Parcela, PlanRotacion
from modules import datos_ambientales as amb_mod
from modules import historial as hist_mod
from modules import lenguaje_sencillo
from modules import motor_agronomico as motor
from modules import simulador
from utils.calculos import MESES_L, QUINTAL_KG, completar_clima

PRIORIDADES = {
    "tierra": {"nombre": "Cuidar mi tierra", "icono": "🌱", "pesos": {"suelo": 5, "agua": 2, "clima": 2, "sanidad": 4, "ingresos": 2}},
    "seguro": {"nombre": "No arriesgar mi cosecha", "icono": "🛡️", "pesos": {"suelo": 2, "agua": 2, "clima": 5, "sanidad": 3, "ingresos": 3}},
    "agua": {"nombre": "Ahorrar agua", "icono": "💧", "pesos": {"suelo": 2, "agua": 5, "clima": 3, "sanidad": 3, "ingresos": 2}},
}
NOMBRES_CRITERIO = {"suelo": "Conservación del suelo", "agua": "Uso del agua de lluvia", "clima": "Adaptación al clima",
                    "sanidad": "Sanidad (plagas y enfermedades)"}


@dataclass
class Opciones:
    pesos: dict = field(default_factory=lambda: dict(PRIORIDADES["tierra"]["pesos"]))
    n_ciclos: int = 4
    cultivos: list[str] | None = None      # claves permitidas (None = todo el catálogo)
    mes_inicio: int | None = None           # None = mes actual
    exigir_leguminosa: bool = True
    modo_lluvia: str = "auto"
    escenario: str | None = None
    tipo: str = "anual"                     # "anual" (12 meses, 3 etapas) | "rotacion" (3-4 cultivos, varios años)

    @property
    def es_anual(self) -> bool:
        return self.tipo == "anual"


def mes_inicio_sugerido(anual: bool, hoy=None) -> int:
    """Plan anual: empieza con las lluvias (octubre). Si ya estamos entre octubre y diciembre, empieza este mes."""
    from datetime import date
    m = (hoy or date.today()).month - 1
    if not anual:
        return m
    inicio = motor.PLAN_ANUAL["mes_inicio_sugerido"]
    return m if inicio <= m <= inicio + 2 else inicio


def ajustar_pesos(pesos: dict, problemas: list[str]) -> tuple[dict, list[str]]:
    """Los problemas que observó el agricultor refuerzan ciertos criterios (trazabilidad: se informan)."""
    p, notas = dict(pesos), []
    for prob, crit, extra, txt in (("suelo_cansado", "suelo", 2, "la tierra ya no produce como antes"),
                                   ("erosion", "suelo", 1, "hay erosión"),
                                   ("falta_agua", "agua", 2, "falta agua en verano"),
                                   ("heladas", "clima", 1, "caen heladas")):
        if prob in problemas:
            p[crit] = p.get(crit, 0) + extra
            notas.append(f"Se dio más peso a «{NOMBRES_CRITERIO[crit]}» porque indicaste que {txt}.")
    return p, notas


def preparar(parcela: Parcela, op: Opciones, forzar: bool = False) -> dict:
    """Reúne historial, datos ambientales, clima y suelo, y arma el contexto del motor."""
    amb = amb_mod.obtener(parcela, forzar)
    clima = amb_mod.clima_parcela(parcela, amb, op.modo_lluvia)
    suelo = amb_mod.suelo_parcela(parcela, amb)
    historial = hist_mod.listar(parcela.id_parcela)
    problemas = list(parcela.lista_problemas)
    if getattr(parcela, "drenaje", None) == "empoza" and "encharcamiento" not in problemas:
        problemas.append("encharcamiento")  # «se empoza el agua» activa la regla R07
    meses = simulador.aplicar_clima(clima["meses_base"], op.escenario)
    if "heladas" in problemas:  # la parcela está en una zona de heladas: más fría que el promedio de la celda
        meses = [m | {"tmin": m["tmin"] - 1.5} for m in meses]
    ctx = motor.Contexto(clima=completar_clima(meses), altitud=clima["altitud"], textura=suelo["textura"], ph=suelo["ph"],
                         materia_organica=suelo["materia_organica"], pendiente=suelo["pendiente"], agua=parcela.disponibilidad_agua,
                         mes_inicio=mes_inicio_sugerido(op.es_anual) if op.mes_inicio is None else op.mes_inicio,
                         historial=[h["cultivo"] for h in historial][-3:], problemas=problemas,
                         escenario=op.escenario, exigir_leguminosa=op.exigir_leguminosa)
    cultivos = simulador.aplicar_cultivos(hist_mod.catalogo(op.cultivos), op.escenario)
    return {"amb": amb, "clima": clima, "suelo": suelo, "historial": historial, "ctx": ctx, "cultivos": cultivos}


def confianza(prep: dict, alt: dict | None = None) -> dict:
    """Nivel de confianza según la calidad de la información disponible (13.5, RNF-11)."""
    pts, faltante = 100, []
    cl, su = prep["clima"], prep["suelo"]
    if cl["fuente"] == "Estimación de referencia":
        pts -= 25; faltante.append("No se pudo consultar el clima de NASA POWER: se usó una estimación por cantón.")
    elif cl["fuente"] != "NASA POWER":
        pts -= 15; faltante.append("NASA POWER no respondió: se usaron datos NASA guardados de Riobamba, no del punto exacto de la parcela.")
    elif cl["discrepancia_lluvia"] and cl["discrepancia_lluvia"] > 0.4:
        pts -= 12; faltante.append(f"La lluvia de NASA POWER ({cl['lluvia_nasa']:,.0f} mm) difiere {cl['discrepancia_lluvia']:.0%} de la referencia local "
                                   f"({cl['lluvia_ref']:,.0f} mm): se usó un promedio de ambas. Un pluviómetro en la finca mejoraría el cálculo.".replace(",", "."))
    if cl["fuente_altitud"] != "NASA SRTM":
        pts -= 10; faltante.append("No se obtuvo la altitud exacta (NASA SRTM): se usó la del cantón más cercano.")
    for k, nombre in (("ph", "pH"), ("textura", "textura"), ("materia_organica", "materia orgánica")):
        f = su["fuentes"][k]
        if f == "supuesto":
            pts -= 8; faltante.append(f"No se conoce el {nombre} del suelo: se asumió un valor típico.")
        elif f == "SoilGrids":
            pts -= 3
    if su["fuentes"]["pendiente"] == "supuesto":
        pts -= 5; faltante.append("No se conoce la pendiente del terreno.")
    if any(f == "SoilGrids" for f in su["fuentes"].values()):
        faltante.append("El suelo se estimó con SoilGrids (resolución de 250 m): un análisis de laboratorio sería más exacto.")
    if not prep["historial"]:
        pts -= 10; faltante.append("No hay historial de cultivos de la parcela.")
    pts -= 10
    faltante.append("Los parámetros de los cultivos son referenciales y aún no los validan los especialistas del equipo (RN-10).")
    if alt and any(x["f_alt"] < 1 for x in alt["ciclos"]):
        pts -= 5
    nivel = "Alta" if pts >= 75 else "Media" if pts >= 55 else "Baja"
    return {"nivel": nivel, "puntos": max(pts, 0), "faltante": faltante}


def _nombre(c):
    return c["nombre"].split(" (")[0]


def _construir_respaldo_satelital(alt: dict, prep: dict) -> list[str]:
    """Evidencia satelital NASA concreta que justifica la recomendación (Vista Técnica)."""
    cl, su, amb = prep["clima"], prep["suelo"], prep["amb"]
    ndvi_data = cl.get("ndvi") or amb.get("NASA NDVI")
    gpm_data = cl.get("gpm") or amb.get("NASA GPM")
    smap_data = cl.get("smap") or amb.get("NASA SMAP")

    evidencias = []
    if gpm_data:
        picos = ", ".join(gpm_data["meses_pico_nombres"][:3]) or "temporada lluviosa"
        evidencias.append(
            f"GPM IMERG (~10 km) + NASA POWER: {cl['lluvia_anual']:,.0f} mm/año y ~{gpm_data['dias_lluvia_intensa_anual']:.0f} "
            f"días/año de lluvia intensa (pico en {picos}, lavado {gpm_data['riesgo_lavado']}); la lluvia cubre "
            f"{alt['puntajes']['agua']:.0f} % de la demanda hídrica del plan.".replace(",", ".")
        )
    else:
        evidencias.append(
            f"NASA POWER: {cl['lluvia_anual']:,.0f} mm/año cubren {alt['puntajes']['agua']:.0f} % de la demanda hídrica de la secuencia.".replace(",", ".")
        )

    if smap_data:
        evidencias.append(
            f"NASA SMAP (9–36 km): humedad superficial actual de {smap_data['humedad_superficial_pct']:.0f} % "
            f"(anomalía hídrica {smap_data['anomalia_hidrica_pct']:+.1f} %, estado {smap_data['estado_hidrico']}), "
            "calibrando la reserva de agua inicial y los meses críticos."
        )

    evidencias.append(
        f"NASA SRTM (30 m): altitud de {cl['altitud']:,.0f} m ({cl['fuente_altitud']}) y pendiente de {su['pendiente']:.1f} % "
        f"(riesgo de erosión en ladera {su.get('riesgo_erosion_ladera', 'moderado').replace('_', ' ')}, LS {su.get('factor_ls', 1.0)}).".replace(",", ".")
    )

    if ndvi_data:
        meses_crit = ", ".join(ndvi_data["meses_criticos_nombres"]) or "ninguno"
        evidencias.append(
            f"MODIS/Landsat/Sentinel-2 NDVI (30–250 m): promedio anual {ndvi_data['ndvi_promedio']:.2f} "
            f"(actual {ndvi_data['ndvi_actual']:.2f}); suelo desnudo detectado en {meses_crit} (riesgo {ndvi_data['riesgo_erosion_ndvi']}), "
            "lo que justifica incluir cobertura vegetal."
        )
    return evidencias


def _construir_validar_campo() -> list[str]:
    """Limitaciones de observación satelital y puntos obligatorios de verificación en campo."""
    return [
        "Plagas y patógenos subterráneos: los sensores satelitales no detectan gusano blanco, nematodos ni pudriciones en raíz; inspeccionar al preparar el lote.",
        "Compactación y micro-drenaje: las escalas de 30–250 m no captan sectores puntuales compactados ni pozas locales dentro de la parcela.",
        "Disponibilidad real de riego y laboratorio: validar turnos efectivos de agua con la junta y contrastar pH/MO estimados con análisis de suelo local.",
    ]


def explicar(alt: dict, prep: dict, area: float) -> dict:
    """Motivos, ventajas, limitaciones, condiciones, respaldo satelital y validación en campo (RF-11, 13.5)."""
    ctx, ciclos, sc = prep["ctx"], alt["ciclos"], alt["puntajes"]
    ventajas, limites, condiciones = [], [], []
    for x in ciclos:
        a, c = x["anterior"], x["cultivo"]
        if a and a["n_aporte_kg_ha"] >= 30 and c["n_demanda_kg_ha"] >= 70:
            ventajas.append(f"{a['emoji']} {_nombre(a)} deja ~{a['n_aporte_kg_ha']} kg de nitrógeno/ha: {c['emoji']} {_nombre(c)} necesita menos urea "
                            f"(ahorro ≈ ${x['ahorro_n'] * area:,.0f}).")
    papas = [c for c in alt["secuencia"] if c["familia"] == "Solanáceas"]
    if papas:
        ventajas.append("La papa descansa al menos 2 ciclos: se corta el ciclo del gusano blanco, del nematodo y de la lancha (regla R02).")
    if alt["diversidad"] == 1:
        ventajas.append(f"{len(alt['secuencia'])} familias botánicas distintas: menos plagas compartidas.")
    if sc["agua"] >= 70:
        ventajas.append(f"La lluvia cubre el {sc['agua']:.0f} % del agua que necesitan los cultivos.")
    if alt["erosion"] < 0.35:
        ventajas.append("Cultivos con buena cobertura: bajo riesgo de erosión.")
    for x in ciclos:
        c = x["cultivo"]
        if x["deficit"] > x["demanda"] * 0.15:
            meses = sorted(set(x["meses_secos"]))
            limites.append(f"{c['emoji']} {_nombre(c)} puede sufrir falta de agua"
                           f"{' en ' + ', '.join(MESES_L[m] for m in meses[:3]) if meses else ''} (pérdida estimada {1 - x['f_agua']:.0%}).")
        if x["f_helada"] < 0.92:
            mh = sorted(set(x["meses_helada"]))
            cuando = ", ".join(MESES_L[m] for m in mh) if len(mh) <= 3 else "varios meses del ciclo"
            limites.append(f"{c['emoji']} {_nombre(c)} tiene riesgo de helada en {cuando} (pérdida estimada {1 - x['f_helada']:.0%}).")
        if x["f_alt"] < 1:
            limites.append(f"{_nombre(c)} está al límite de su rango de altitud ({c['altitud_min']}–{c['altitud_max']} m).")
        if x["f_ph"] < 1:
            limites.append(f"El pH {ctx.ph:.1f} no es el ideal para {_nombre(c)} ({c['ph_min']}–{c['ph_max']}).")
        if x["margen"] < 0:
            limites.append(f"{_nombre(c)} podría dar pérdida económica con los precios de referencia.")
    if alt["erosion"] >= 0.5:
        limites.append("Riesgo de erosión alto por el laboreo y la pendiente.")
    if alt["riego_total"] > 30:
        condiciones.append(f"Disponer de unos {alt['riego_total'] * 10 * area:,.0f} m³ de agua de riego en toda la rotación.".replace(",", "."))
    if ctx.ph < 5.5 and any(c["n_aporte_kg_ha"] >= 30 for c in alt["secuencia"]):
        condiciones.append("Aplicar cal agrícola o dolomita antes de sembrar la leguminosa.")
    if ctx.pendiente > 12:
        condiciones.append("Sembrar en curvas de nivel y con barreras vivas (sigse, pasto) en los cultivos que remueven mucho el suelo.")
    if papas:
        condiciones.append("Usar semilla de papa certificada y trampas contra el gusano blanco.")
    if any(c["n_aporte_kg_ha"] >= 30 for c in alt["secuencia"]):
        condiciones.append("Incorporar al suelo los residuos de la leguminosa después de la cosecha.")
    precoces = [c["uso_anual"] for c in alt["secuencia"] if "precoz" in c.get("uso_anual", "")]
    if precoces:
        condiciones.append("El plan anual es ajustado: usar " + ", ".join(p.lower() for p in precoces) +
                           " y sembrar apenas termine la etapa anterior.")
    mejores = sorted(sc, key=lambda k: -sc[k] * (1 + alt["pesos"].get(k, 0)))[:2]
    motivos = [f"Destaca en {NOMBRES_CRITERIO[k].lower()} ({sc[k]:.0f}/100)." for k in mejores]
    motivos.append("Cumple todas las restricciones agronómicas esenciales (R01–R07).")

    def unicos(xs):
        return list(dict.fromkeys(xs))

    ventajas, limites, condiciones = unicos(ventajas), unicos(limites), unicos(condiciones)
    return {
        "motivos": motivos,
        "ventajas": ventajas,
        "limitaciones": limites or ["No se identificaron limitaciones importantes con los datos disponibles."],
        "condiciones": condiciones,
        "respaldo_satelital": _construir_respaldo_satelital(alt, prep),
        "validar_en_campo": _construir_validar_campo(),
    }


def _cultivo_testigo(prep: dict) -> dict:
    """Selecciona el cultivo base del manejo actual (último sembrado o papa por defecto)."""
    if prep["historial"]:
        return prep["historial"][-1]["cultivo"]
    cat_completo = {c["id"]: c for c in hist_mod.catalogo()}
    if "papa" in cat_completo:
        return cat_completo["papa"]
    return prep["cultivos"][0] if prep["cultivos"] else next(iter(cat_completo.values()))


def calcular_testigo(prep: dict, pesos: dict, anual: bool = True, n_ciclos: int = 4) -> dict:
    """Escenario testigo («Manejo Actual / Sin Rotación»): repetir el mismo cultivo todo el ciclo."""
    base = _cultivo_testigo(prep)
    ctx = prep["ctx"]
    if anual:
        seq = []
        for e in motor.ETAPAS:
            v = motor.variante_anual(base, e, ctx.altitud)
            if v is None:
                ratio = e["meses"] / max(base["ciclo_meses"], 1)
                v = base | {
                    "ciclo_meses": e["meses"],
                    "rendimiento_t_ha": base["rendimiento_t_ha"] * ratio,
                    "costo_usd_ha": base["costo_usd_ha"] * ratio,
                    "uso_anual": f"{_nombre(base)} (sin rotación)",
                    "etapa": e["n"],
                    "etapa_nombre": e["nombre"],
                    "etapa_rol": e["rol"],
                }
            seq.append(v)
        ev = motor.evaluar_secuencia(seq, ctx, pesos, prep=0)
    else:
        seq = [base] * n_ciclos
        ev = motor.evaluar_secuencia(seq, ctx, pesos)

    ev["cultivo_base"] = base
    ev["nombre_cultivo"] = _nombre(base)
    ev["etiqueta"] = f"Si repites { _nombre(base).lower() } todo el año (sin rotación)"
    return ev


def comparar_con_testigo(alt: dict, testigo: dict, area: float) -> dict:
    """Calcula cuánto mejora una alternativa recomendada frente al escenario testigo sin rotación."""
    sc_a, sc_t = alt["puntajes"], testigo["puntajes"]
    suelo_t = max(sc_t["suelo"], 1.0)
    mejora_suelo_pts = round(sc_a["suelo"] - sc_t["suelo"], 1)
    mejora_suelo_pct = round(((sc_a["suelo"] - sc_t["suelo"]) / suelo_t) * 100)
    mejora_sanidad_pts = round(sc_a["sanidad"] - sc_t["sanidad"], 1)
    mejora_agua_pts = round(sc_a["agua"] - sc_t["agua"], 1)
    mejora_total = round(alt["total"] - testigo["total"], 1)

    n_testigo = sum(x["n_aplicar"] for x in testigo["ciclos"])
    n_plan = sum(x["n_aplicar"] for x in alt["ciclos"])
    ahorro_n_kg_ha = max(0.0, n_testigo - n_plan)
    ahorro_urea_sacos = round(ahorro_n_kg_ha * area / 0.46 / 50, 1)
    ahorro_abono_usd = round(ahorro_n_kg_ha * motor.PARAM["precio_n_usd_kg"] * area)
    ahorro_abono_pct = round((ahorro_n_kg_ha / n_testigo) * 100) if n_testigo > 0 else 0

    cult_base = testigo.get("nombre_cultivo", "el mismo cultivo").lower()
    partes = []
    if mejora_suelo_pct > 0:
        partes.append(f"+{mejora_suelo_pct} % salud de tu tierra")
    if ahorro_abono_usd >= 5:
        partes.append(f"ahorro estimado de ${ahorro_abono_usd:,} en abono ({ahorro_urea_sacos:.1f} sacos de urea)".replace(",", ".").replace(".", ",", 1) if False else f"ahorro estimado de ${ahorro_abono_usd:,} en abono".replace(",", "."))
    elif ahorro_abono_pct > 0:
        partes.append(f"ahorro estimado de {ahorro_abono_pct} % en abono")
    if not partes:
        partes.append(f"+{max(0, round(mejora_sanidad_pts))} puntos en control de plagas")

    resumen_sencillo = " y ".join(partes) + f" frente a repetir {cult_base} todo el año."
    resumen_tecnico = (
        f"Suelo {mejora_suelo_pct:+d} % ({mejora_suelo_pts:+.1f} pts) · Sanidad {mejora_sanidad_pts:+.1f} pts · "
        f"Puntaje global {mejora_total:+.1f} pts · Ahorro {ahorro_n_kg_ha:.0f} kg N/ha (${ahorro_abono_usd:,} en la parcela) "
        f"vs. monocultivo continuo de {cult_base}."
    ).replace(",", ".")

    return {
        "cultivo_testigo": testigo.get("nombre_cultivo", "Papa"),
        "puntaje_testigo": round(testigo["total"], 1),
        "suelo_testigo": round(sc_t["suelo"], 1),
        "sanidad_testigo": round(sc_t["sanidad"], 1),
        "agua_testigo": round(sc_t["agua"], 1),
        "mejora_suelo_pts": mejora_suelo_pts,
        "mejora_suelo_pct": mejora_suelo_pct,
        "mejora_sanidad_pts": mejora_sanidad_pts,
        "mejora_agua_pts": mejora_agua_pts,
        "mejora_total": mejora_total,
        "ahorro_n_kg_ha": round(ahorro_n_kg_ha, 1),
        "ahorro_urea_sacos": ahorro_urea_sacos,
        "ahorro_abono_usd": ahorro_abono_usd,
        "ahorro_abono_pct": ahorro_abono_pct,
        "resumen_sencillo": resumen_sencillo,
        "resumen_tecnico": resumen_tecnico,
    }


def generar(id_parcela: int, op: Opciones, forzar_datos: bool = False) -> dict:
    """CU-03: genera hasta 3 alternativas explicadas para la parcela y su escenario testigo."""
    parcela = amb_mod_parcela(id_parcela)
    prep = preparar(parcela, op, forzar_datos)
    pesos, notas_pesos = ajustar_pesos(op.pesos, prep["ctx"].problemas)
    testigo = calcular_testigo(prep, pesos, anual=op.es_anual, n_ciclos=op.n_ciclos)
    res = (motor.optimizar_anual(prep["cultivos"], prep["ctx"], pesos) if op.es_anual
           else motor.optimizar(prep["cultivos"], prep["ctx"], pesos, op.n_ciclos))
    alternativas = []
    for i, a in enumerate(res["alternativas"]):
        a["pesos"] = pesos
        a["nombre"] = "ABC"[i]
        a["explicacion"] = explicar(a, prep, parcela.superficie)
        a["confianza"] = confianza(prep, a)
        a["vs_testigo"] = comparar_con_testigo(a, testigo, parcela.superficie)
        a["guia"] = lenguaje_sencillo.guia(a, prep, parcela.superficie)
        a["guia"]["vs_testigo"] = a["vs_testigo"]
        alternativas.append(a)
    return {"parcela": parcela, "prep": prep, "alternativas": alternativas, "testigo": testigo,
            "evaluadas": res["evaluadas"], "descartadas": res["descartadas"],
            "excluidos_altitud": res["excluidos_altitud"], "pesos": pesos, "notas_pesos": notas_pesos,
            "avisos": prep["amb"]["avisos"], "opciones": op, "confianza": confianza(prep),
            "sin_resultado": not alternativas, "anual": op.es_anual,
            "etapas_sin_cultivo": res.get("etapas_sin_cultivo", [])}


def amb_mod_parcela(id_parcela: int) -> Parcela:
    from modules import parcelas
    p = parcelas.obtener(id_parcela)
    if p is None:
        raise ValueError(f"No existe la parcela {id_parcela}")
    return p


def evaluar_en(prep: dict, secuencias: list[list[str]], pesos: dict, anual: bool = False) -> list[dict]:
    """Vuelve a evaluar secuencias concretas (por ejemplo, las alternativas base) en otro contexto."""
    cat = {c["id"]: c for c in prep["cultivos"]}
    if anual:
        alt = prep["ctx"].altitud
        return [motor.evaluar_secuencia([motor.variante_anual(cat[k], e, alt) for k, e in zip(s, motor.ETAPAS)], prep["ctx"], pesos, prep=0)
                for s in secuencias]
    return [motor.evaluar_secuencia([cat[k] for k in s], prep["ctx"], pesos) for s in secuencias]


def simular(id_parcela: int, op: Opciones, base: dict, escenario: str, usar_smap: bool = False) -> dict:
    """CU-05: compara las alternativas base con el mismo plan bajo un escenario hipotético."""
    op_e = Opciones(**{**op.__dict__, "escenario": escenario})
    parcela = amb_mod_parcela(id_parcela)
    prep = preparar(parcela, op_e)
    smap_data = prep["amb"].get("NASA SMAP")
    if usar_smap and smap_data:
        meses_smap = simulador.aplicar_smap(simulador.aplicar_clima(prep["clima"]["meses_base"], escenario), smap_data)
        if "heladas" in prep["ctx"].problemas:
            meses_smap = [m | {"tmin": m["tmin"] - 1.5} for m in meses_smap]
        prep["ctx"].clima = completar_clima(meses_smap)
    pesos, _ = ajustar_pesos(op.pesos, prep["ctx"].problemas)
    secs = [[c["id"] for c in a["secuencia"]] for a in base["alternativas"]]
    evals = evaluar_en(prep, secs, pesos, op.es_anual)
    mejor = (motor.optimizar_anual(prep["cultivos"], prep["ctx"], pesos, top=1) if op.es_anual
             else motor.optimizar(prep["cultivos"], prep["ctx"], pesos, op.n_ciclos, top=1))["alternativas"]
    return {
        "escenario": escenario,
        "info": simulador.ESCENARIOS[escenario],
        "aviso": simulador.AVISO,
        "smap": simulador.diagnosticar_smap(smap_data),
        "gpm": prep["clima"].get("gpm"),
        "filas": [{"nombre": a["nombre"], "base": a, "escenario": e} for a, e in zip(base["alternativas"], evals)],
        "mejor_en_escenario": mejor[0] if mejor else None,
    }


def resumen_ciclos(alt: dict, area: float, mes_inicio: int, anio_inicio: int) -> list[dict]:
    """Ciclos con fechas reales y cantidades para la superficie de la parcela."""
    out = []
    for x in alt["ciclos"]:
        c = x["cultivo"]
        def fecha(rel):
            t = mes_inicio + rel
            return f"{MESES_L[t % 12]} {anio_inicio + t // 12}"
        kg = c["rendimiento_t_ha"] * 1000 * x["rendimiento_rel"] * area
        out.append({"cultivo": c, "siembra": fecha(x["inicio"]), "cosecha": fecha(x["fin"]), "kg": kg, "quintales": kg / QUINTAL_KG,
                    "rend_t_ha": c["rendimiento_t_ha"] * x["rendimiento_rel"], "margen": x["margen"] * area,
                    "urea_sacos": x["n_aplicar"] * area / 0.46 / 50, "n_kg_ha": x["n_aplicar"], "riego_m3": x["riego"] * 10 * area,
                    "meses_helada": sorted(set(x["meses_helada"])), "meses_secos": sorted(set(x["meses_secos"])), "ciclo": x})
    return out


# ------------------------------------------------------------------ RF-16: planes guardados
def guardar(resultado: dict, id_tecnico: int | None = None) -> list[int]:
    p, ids = resultado["parcela"], []
    with sesion() as s:
        for a in resultado["alternativas"]:
            detalle = {"puntajes": a["puntajes"], "margen_anual_ha": a["margen_anual"], "meses": a["meses"], "pesos": a["pesos"],
                       "explicacion": a["explicacion"], "confianza": a["confianza"], "riego_total_mm": a["riego_total"],
                       "vs_testigo": a.get("vs_testigo"),
                       "mes_inicio": resultado["prep"]["ctx"].mes_inicio, "guia": a.get("guia"),
                       "fuentes": {"clima": resultado["prep"]["clima"]["fuente"], "altitud": resultado["prep"]["clima"]["fuente_altitud"],
                                   "suelo": resultado["prep"]["suelo"]["fuentes"]}}
            pl = PlanRotacion(id_parcela=p.id_parcela, alternativa=f"Alternativa {a['nombre']}",
                              justificacion=" ".join(a["explicacion"]["motivos"] + a["explicacion"]["ventajas"]),
                              puntuacion=round(a["total"], 1), secuencia=",".join(c["id"] for c in a["secuencia"]),
                              confianza=a["confianza"]["nivel"], escenario=resultado["opciones"].escenario,
                              id_tecnico=id_tecnico, tipo=resultado["opciones"].tipo,
                              detalle=json.dumps(detalle, ensure_ascii=False, default=str))
            s.add(pl)
            s.flush()
            ids.append(pl.id_plan)
    return ids


def listar_planes(id_parcela: int) -> list[dict]:
    with sesion() as s:
        planes = list(s.scalars(select(PlanRotacion).where(PlanRotacion.id_parcela == id_parcela).order_by(PlanRotacion.fecha_generacion.desc())))
        return [{"id_plan": p.id_plan, "fecha": p.fecha_generacion, "alternativa": p.alternativa, "secuencia": p.secuencia.split(","),
                 "puntuacion": p.puntuacion, "confianza": p.confianza, "justificacion": p.justificacion,
                 "id_tecnico": p.id_tecnico, "tipo": p.tipo or "rotacion",
                 "detalle": json.loads(p.detalle)} for p in planes]
