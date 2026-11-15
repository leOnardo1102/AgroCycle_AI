"""Traductor a lenguaje sencillo (Regla de oro del producto).

Todo lo que recibe el agricultor (vista agricultor, WhatsApp, correo, hoja impresa y PDF) sale de aquí,
sin siglas ni jerga científica, y responde a 4 preguntas de campo:
  1. Qué sembrar en orden.   2. Por qué le conviene.   3. Cuánto ahorra.   4. Qué cuidar del clima.
"""
from datetime import date

from utils.calculos import MESES_L, QUINTAL_KG

ORDINAL = ["1ro", "2do", "3ro", "4to", "5to"]
# Palabras que nunca deben llegar al agricultor
JERGA = [
    "PRECTOTCORR", "GWETROOT", "T2M", "pH", "nitrógeno", "evapotranspiración", "leguminosa", "Kc", "ET0",
    "déficit", "SoilGrids", "SRTM", "NDVI", "fijación", "GPM", "IMERG", "SMAP", "MODIS", "Landsat", "Sentinel",
]


def nombre_corto(c: dict) -> str:
    return c["nombre"].split(" (")[0]


def _meses(lista: list[int], maximo: int = 4) -> str:
    ms = sorted(set(lista))
    if not ms:
        return ""
    if len(ms) > maximo:
        return "casi todo el año"
    nombres = [MESES_L[m] for m in ms]
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _nombre_con_uso(c: dict) -> str:
    """«Papa de variedad precoz», «Haba (haba tierna en vaina)» o simplemente «Papa»."""
    base, uso = nombre_corto(c), c.get("uso_anual", "")
    if not uso or uso == base:
        return base
    return uso if uso.lower().startswith(base.lower()) else f"{base} ({uso.lower()})"


def anio_inicio(mes_inicio: int, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    return hoy.year + (1 if mes_inicio < hoy.month - 1 else 0)


def _fecha(rel: int, mes0: int, anio0: int) -> str:
    t = mes0 + rel
    return f"{MESES_L[t % 12]} {anio0 + t // 12}"


def semaforo(valor: float, verde: float = 75, amarillo: float = 55) -> str:
    return "🟢" if valor >= verde else "🟡" if valor >= amarillo else "🔴"


def traducir_ndvi(ndvi_data: dict | None) -> str:
    """Convierte el análisis satelital de cobertura vegetal a lenguaje práctico de campo."""
    if not ndvi_data:
        return "Cobertura de la tierra: Conviene mantener la tierra cubierta en verano con cultivo de cobertura o rastrojo."
    meses_desnudos = ndvi_data.get("meses_suelo_desnudo") or []
    if meses_desnudos:
        cuales = _meses(meses_desnudos)
        return (
            f"Cobertura de la tierra: Suelo descubierto en verano ({cuales}), "
            "conviene sembrar cultivo de cobertura para que el viento y la lluvia no se lleven la tierra."
        )
    return "Cobertura de la tierra: Buena cobertura vegetal durante el año, con bajo riesgo de que el suelo quede descubierto."


def _respaldo_nasa_sencillo(alt: dict, prep: dict) -> list[str]:
    """Explica en lenguaje de campo qué datos satelitales respaldan la selección de cultivos."""
    clima = prep.get("clima", {})
    suelo = prep.get("suelo", {})
    amb = prep.get("amb", {})
    ndvi_data = clima.get("ndvi") or amb.get("NASA NDVI")
    gpm_data = clima.get("gpm") or amb.get("NASA GPM")
    smap_data = clima.get("smap") or amb.get("NASA SMAP")

    lluvia_anual = round(clima.get("lluvia_anual", 600))
    respaldo = []

    if gpm_data and gpm_data.get("riesgo_lavado") == "alto":
        picos = _meses(gpm_data.get("meses_pico_intensidad") or [])
        extra = f" con aguaceros fuertes en {picos}" if picos else " con aguaceros fuertes"
        respaldo.append(
            f"Lluvia medida desde el satélite: caen unos {lluvia_anual:,} mm al año{extra}; "
            "por eso el plan prioriza cultivos que protegen la tierra del lavado.".replace(",", ".")
        )
    else:
        lluvia10 = round(alt["puntajes"]["agua"] / 10)
        respaldo.append(
            f"Lluvia medida desde el satélite: unos {lluvia_anual:,} mm al año, "
            f"que alcanzan para cubrir {lluvia10} de cada 10 partes del agua que piden estos cultivos.".replace(",", ".")
        )

    if smap_data:
        estado = smap_data.get("estado_hidrico", "normal")
        pct = round(smap_data.get("humedad_superficial_pct", 54))
        if estado == "deficit":
            msg_h = f"humedad baja ({pct} %): se incluyen siembras que resisten mejor la falta de agua."
        elif estado == "exceso":
            msg_h = f"tierra bien húmeda ({pct} %): conviene vigilar que no se empoce el agua."
        else:
            msg_h = f"humedad en nivel normal ({pct} %): buena condición para arrancar la siembra."
        respaldo.append(f"Humedad de la tierra por satélite: {msg_h}")

    pend = float(suelo.get("pendiente", 8.0))
    if pend >= 12:
        respaldo.append(
            f"Inclinación del terreno ({pend:.0f} %): al ser ladera fuerte, se eligen plantas de buena raíz "
            "y cobertura para frenar la pérdida de tierra."
        )
    else:
        respaldo.append(
            f"Inclinación del terreno ({pend:.0f} %): pendiente suave que permite alternar cultivos sin desgastar tanto la tierra."
        )

    respaldo.append(traducir_ndvi(ndvi_data))
    return respaldo


def _validar_campo_sencillo(prep: dict) -> list[str]:
    """Recuerda qué aspectos reales del lote no ve el satélite y deben validarse en campo."""
    return [
        "Plagas bajo tierra: el satélite no detecta gusano blanco ni enfermedades en la raíz; revisa el terreno al arar.",
        "Partes duras o encharcadas: camina el lote para ver si hay zonas compactadas o donde se empoza el agua.",
        "Turnos de agua y suelo real: confirma tus turnos reales con la junta de riego y verifica la tierra junto al técnico.",
    ]


def guia(alt: dict, prep: dict, area: float) -> dict:
    """Plan explicado para el agricultor, sin tecnicismos."""
    ctx = prep["ctx"]
    mes0 = ctx.mes_inicio
    anio0 = anio_inicio(mes0)
    sc = alt["puntajes"]
    ciclos = alt["ciclos"]

    # 1. Qué sembrar en orden
    pasos = []
    for i, x in enumerate(ciclos):
        c = x["cultivo"]
        kg = c["rendimiento_t_ha"] * 1000 * x["rendimiento_rel"] * area
        sacos = x["n_aplicar"] * area / 0.46 / 50
        if x["n_residual"] >= 30 and sacos < 0.3:
            abono = f"Casi no necesita urea: {nombre_corto(x['anterior']).lower()} dejó abono natural en la tierra."
        elif sacos >= 0.3:
            abono = f"Abono: unos {sacos:.1f} sacos de urea de 50 kg".replace(".", ",") + \
                    (f" (menos de lo normal gracias a {nombre_corto(x['anterior']).lower()})." if x["n_residual"] >= 30 else ".")
        else:
            abono = "Casi no necesita urea."
        alertas = []
        if x["meses_helada"]:
            alertas.append(f"Cuidado con heladas en {_meses(x['meses_helada'])}.")
        if x["meses_secos"]:
            alertas.append(("Riega sobre todo en " if ctx.agua != "secano" else "Puede faltar lluvia en ") + _meses(x["meses_secos"][:3]) + ".")
        cantidad = f"unas {kg / 1000:.0f} toneladas de forraje" if c.get("forraje") else f"unos {kg / QUINTAL_KG:,.0f} quintales".replace(",", ".")
        etapa = (f"Etapa {c['etapa']} · {c['etapa_nombre']} (mes {x['inicio'] + 1} a {x['fin'] + 1})" if c.get("etapa") else "")
        pasos.append({"n": i + 1, "orden": ORDINAL[i], "emoji": c["emoji"], "cultivo": nombre_corto(c),
                      "uso": c.get("uso_anual", ""), "etapa": etapa, "nombre_completo": _nombre_con_uso(c),
                      "siembra": _fecha(x["inicio"], mes0, anio0), "cosecha": _fecha(x["fin"], mes0, anio0),
                      "quintales": kg / QUINTAL_KG, "cantidad": cantidad, "abono": abono,
                      "consejo": c.get("consejo_practico", ""), "alertas": alertas, "color": c.get("color", "#2f6b3a")})
    anual = any(c.get("etapa") for c in alt["secuencia"])
    orden = " → ".join(f"{p['orden']} {p['cultivo']}" for p in pasos)

    # 2. Por qué le conviene ese orden
    por_que = []
    for x in ciclos:
        a, c = x["anterior"], x["cultivo"]
        if a and a["n_aporte_kg_ha"] >= 30 and c["n_demanda_kg_ha"] >= 60:
            por_que.append(f"{a['emoji']} {nombre_corto(a)} deja abono natural en la tierra: en la siguiente siembra "
                           f"({nombre_corto(c).lower()}) gastas menos en fertilizante.")
            break
    if any(c["familia"] == "Solanáceas" for c in alt["secuencia"]) or any(h["familia"] == "Solanáceas" for h in ctx.historial[-1:]):
        por_que.append("Cambiar de cultivo corta las plagas: el gusano blanco y la lancha de la papa no encuentran comida.")
    if any(c["cobertura"] >= 3 for c in alt["secuencia"]):
        cub = next(c for c in alt["secuencia"] if c["cobertura"] >= 3)
        por_que.append(f"{cub['emoji']} {nombre_corto(cub)} cubre bien la tierra y la protege de la lluvia y del viento.")
    if any(c["familia"] == "Pradera" for c in alt["secuencia"]):
        por_que.append("El pasto con trébol deja descansar la tierra y además da comida para tus animales.")
    if len({c["familia"] for c in alt["secuencia"]}) == len(alt["secuencia"]):
        por_que.append("Cada siembra es de un tipo distinto de planta: la tierra no se cansa tanto.")

    # 3. Ahorro de agua y abono
    mo_n = min(60, ctx.materia_organica * 12)
    base = sum(x["n_aplicar"] + min(x["n_residual"], max(0, x["cultivo"]["n_demanda_kg_ha"] - mo_n)) for x in ciclos)
    usado = sum(x["n_aplicar"] for x in ciclos)
    ahorro = []
    if base > 0 and base > usado:
        pct = round((1 - usado / base) * 100)
        ahorro.append(f"Casi no necesitarás abono químico: ahorras cerca del {pct} % gracias al abono natural que dejan las plantas." if pct >= 90 else
                      f"Ahorra cerca del {pct} % de abono químico gracias al abono natural que dejan las plantas.")
    lluvia10 = round(sc["agua"] / 10)
    if lluvia10 >= 7:
        ahorro.append(f"Aprovecha bien la lluvia: cubre {lluvia10} de cada 10 partes del agua que necesitan tus cultivos.")
    elif ctx.agua != "secano":
        ahorro.append(f"La lluvia cubre {lluvia10} de cada 10 partes del agua: el resto tendrás que regarlo.")
    else:
        ahorro.append(f"La lluvia cubre {lluvia10} de cada 10 partes del agua: siembra apenas empiecen las lluvias.")

    # 4. Cuidado clave del clima (con acción práctica)
    clima = []
    helada = [m for x in ciclos for m in x["meses_helada"]]
    secos = [m for x in ciclos for m in x["meses_secos"]]
    if helada:
        cuando = _meses(helada)
        clima.append(("Puede helar casi todo el año" if cuando == "casi todo el año" else f"Cuidado con heladas en {cuando}") +
                     ", sobre todo en madrugadas despejadas: aporca bien las matas y, si la tarde está despejada y fría, "
                     "riega antes de que anochezca.")
    if secos:
        clima.append(f"En {_meses(secos)} suele faltar agua: " +
                     ("asegura tus turnos de riego para esos meses." if ctx.agua != "secano" else "siembra con las primeras lluvias y cubre la tierra con paja."))
    lluviosos = [i for i, m in enumerate(ctx.clima) if m["pe"] > 1.1 * m["et0"]]
    if lluviosos and any(c["familia"] == "Solanáceas" for c in alt["secuencia"]):
        clima.append(f"En {_meses(lluviosos)} llueve más: revisa la papa cada semana por lancha (manchas oscuras en las hojas).")
    ndvi_data = prep.get("clima", {}).get("ndvi")
    if ndvi_data and ndvi_data.get("meses_suelo_desnudo"):
        clima.append(traducir_ndvi(ndvi_data))
    if ctx.pendiente > 12:
        clima.append("Tu terreno es inclinado: siembra en curvas a lo ancho de la pendiente para que la lluvia no se lleve la tierra.")
    if ctx.ph < 5.5:
        leg = next((c for c in alt["secuencia"] if c["n_aporte_kg_ha"] >= 30), None)
        clima.append("Tu tierra es ácida: pon cal agrícola un mes antes de sembrar" + (f" {nombre_corto(leg).lower()}." if leg else "."))
    if not clima:
        clima.append("No se esperan problemas fuertes de clima: mantén tu cuidado de siempre.")

    # Semáforos
    conf = alt.get("confianza", {}).get("nivel", "Media")
    semaforos = [
        {"luz": semaforo(sc["suelo"]), "titulo": "Tu tierra", "texto": "Mejora" if sc["suelo"] >= 75 else "Se mantiene" if sc["suelo"] >= 55 else "Se desgasta"},
        {"luz": semaforo(sc["agua"], 70, 45), "titulo": "Agua", "texto": "La lluvia alcanza casi todo" if sc["agua"] >= 70 else "Necesitarás algo de riego" if sc["agua"] >= 45 else "Necesitarás mucho riego"},
        {"luz": semaforo(sc["clima"]), "titulo": "Heladas y sequía", "texto": "Riesgo bajo" if sc["clima"] >= 75 else "Riesgo medio" if sc["clima"] >= 55 else "Riesgo alto"},
        {"luz": {"Alta": "🟢", "Media": "🟡", "Baja": "🔴"}[conf], "titulo": "Seguridad del cálculo",
         "texto": {"Alta": "Buena información", "Media": "Información suficiente", "Baja": "Falta información"}[conf]},
    ]
    mejorar = []
    if not prep["historial"]:
        mejorar.append("Anota lo que sembraste antes en este terreno.")
    if any(f in ("SoilGrids", "supuesto") for f in prep["suelo"]["fuentes"].values()):
        mejorar.append("Un análisis de tu tierra en laboratorio haría el plan más exacto.")
    return {
        "pasos": pasos, "orden": orden, "por_que": por_que[:3], "ahorro": ahorro, "clima": clima[:3],
        "semaforos": semaforos, "mejorar": mejorar, "anios": alt["meses"] / 12,
        "anual": anual, "titulo_pasos": "Qué sembrar mes a mes (plan de 12 meses)" if anual else "Qué sembrar, en orden",
        "periodo": f"de {pasos[0]['siembra']} a {pasos[-1]['cosecha']}" if pasos else "",
        "cobertura_tierra": traducir_ndvi(ndvi_data),
        "respaldo_nasa": _respaldo_nasa_sencillo(alt, prep),
        "validar_campo": _validar_campo_sencillo(prep),
    }


def tiene_jerga(texto: str) -> list[str]:
    import re
    return [p for p in JERGA if re.search(rf"(?<![\w]){re.escape(p)}(?![\w])", texto)]
