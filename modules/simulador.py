"""Simulador de escenarios climáticos HIPOTÉTICOS (RF-14, CU-05, RN-09).
No son pronósticos: solo muestran cómo cambiarían las alternativas si ocurriera la condición.
Conecta también con la humedad superficial y anomalía hídrica de NASA SMAP.
"""
from utils.calculos import clamp

ESCENARIOS = {
    "seco": {"nombre": "Año seco (-30 % lluvia)", "descripcion": "30 % menos lluvia en todos los meses (similar a un año de La Niña fuerte en la sierra)."},
    "lluvioso": {"nombre": "Año lluvioso (+30 % lluvia)", "descripcion": "30 % más lluvia, con más enfermedades por hongos (lancha en papa, mancha de chocolate en haba)."},
    "calor": {"nombre": "Más calor (+1,5 °C)", "descripcion": "Temperaturas 1,5 °C más altas todo el año (tendencia de calentamiento)."},
    "helada": {"nombre": "Heladas fuertes (-2 °C mín.)", "descripcion": "Temperaturas mínimas 2 °C más bajas en los meses secos y despejados."},
    "precio_papa": {"nombre": "Precio de papa -40 %", "descripcion": "Caída del precio de la papa en el mercado (sobreoferta)."},
}
AVISO = "Escenario hipotético: no es un pronóstico meteorológico ni de mercado (RN-09)."


def diagnosticar_smap(smap_data: dict | None) -> dict:
    """Resume el estado hídrico actual de NASA SMAP y qué escenario del simulador sugiere evaluar."""
    if not smap_data:
        return {
            "disponible": False,
            "estado_hidrico": "normal",
            "humedad_superficial_pct": 54.0,
            "anomalia_hidrica_pct": 0.0,
            "escenario_sugerido": "seco",
            "mensaje_tecnico": "Sin lectura SMAP; se recomienda evaluar al menos el escenario de año seco.",
            "mensaje_sencillo": "Conviene revisar qué pasa si falta agua en los meses secos.",
        }

    sup_pct = smap_data.get("humedad_superficial_pct", round(smap_data.get("humedad_superficial", 0.54) * 100, 1))
    anom = smap_data.get("anomalia_hidrica_pct", 0.0)
    estado = smap_data.get("estado_hidrico", "normal")
    sug = smap_data.get("escenario_sugerido", "normal")

    if estado == "deficit":
        msg_tec = (
            f"Déficit hídrico detectado por SMAP ({sup_pct:.0f} % humedad superficial, anomalía {anom:+.1f} %): "
            "priorizar simulación de «Año seco» y verificar turnos de riego."
        )
        msg_sen = "La tierra viene más seca de lo normal: conviene elegir cultivos que aguanten falta de agua."
        esc = "seco"
    elif estado == "exceso":
        msg_tec = (
            f"Superávit hídrico en superficie SMAP ({sup_pct:.0f} % humedad superficial, anomalía {anom:+.1f} %): "
            "priorizar simulación de «Año lluvioso» por riesgo de lancha y encharcamiento."
        )
        msg_sen = "La tierra guarda bastante humedad: vigila encharcamientos y manchas por exceso de lluvia."
        esc = "lluvioso"
    else:
        msg_tec = (
            f"Humedad superficial SMAP en rango normal ({sup_pct:.0f} %, anomalía {anom:+.1f} %): "
            "simular «Año seco» para estrés en verano."
        )
        msg_sen = "La humedad de la tierra está normal para la época."
        esc = sug if sug in ESCENARIOS else "seco"

    return {
        "disponible": True,
        "estado_hidrico": estado,
        "humedad_superficial_pct": sup_pct,
        "anomalia_hidrica_pct": anom,
        "escenario_sugerido": esc,
        "mensaje_tecnico": msg_tec,
        "mensaje_sencillo": msg_sen,
    }


def aplicar_smap(meses: list[dict], smap_data: dict | None) -> list[dict]:
    """Ajusta los primeros meses de lluvia disponible según la anomalía hídrica superficial de SMAP."""
    if not smap_data:
        return [dict(m) for m in meses]
    anom = float(smap_data.get("anomalia_hidrica_pct", 0.0))
    # Solo ajusta si existe anomalía hídrica significativa (|anomalía| >= 5 %)
    if abs(anom) < 5.0:
        return [dict(m) for m in meses]
    factor_base = clamp(1.0 + anom / 100.0 * 0.5, 0.75, 1.25)
    out = []
    for i, m in enumerate(meses):
        copia = dict(m)
        # El peso de la humedad inicial SMAP decae gradualmente en los primeros 3 meses
        if i < 3:
            peso = 1.0 - i * 0.3
            f = 1.0 + (factor_base - 1.0) * peso
            copia["p"] = round(copia["p"] * f, 2)
        out.append(copia)
    return out


def aplicar_clima(meses: list[dict], escenario: str | None) -> list[dict]:
    out = []
    for i, m in enumerate(meses):
        m = dict(m)
        if escenario == "seco":
            m["p"] *= 0.7
        elif escenario == "lluvioso":
            m["p"] *= 1.3
        elif escenario == "calor":
            for k in ("t", "tmin", "tmax"):
                m[k] += 1.5
        elif escenario == "helada" and i in (0, 5, 6, 7, 8, 11):
            m["tmin"] -= 2
        out.append(m)
    return out


def aplicar_cultivos(cultivos: list[dict], escenario: str | None) -> list[dict]:
    if escenario != "precio_papa":
        return cultivos
    return [c | {"precio_usd_kg": c["precio_usd_kg"] * 0.6} if c["id"] == "papa" else c for c in cultivos]
