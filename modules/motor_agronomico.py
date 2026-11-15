"""Motor agronómico (sección 13): restricciones esenciales + puntuación ponderada.

Flujo (13.3): filtrar cultivos -> enumerar secuencias -> descartar las que incumplen restricciones
esenciales -> simular cada ciclo (agua, nitrógeno, heladas, altitud, pH) -> puntuar -> ordenar.
"""
import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

from utils.calculos import clamp

RAIZ = Path(__file__).resolve().parent.parent
REGLAS = json.loads((RAIZ / "data" / "reglas_agronomicas.json").read_text(encoding="utf-8"))
PARAM = REGLAS["parametros"]
SAN = REGLAS["penalizaciones_sanidad"]
CAPACIDAD_SUELO = {"arenoso": 35, "francoarenoso": 55, "franco": 75, "francoarcilloso": 90, "arcilloso": 100}
COBERTURA_RIEGO = {"secano": 0.0, "turnos": 0.5, "completo": 1.0}
CRITERIOS = ["suelo", "agua", "clima", "sanidad", "ingresos"]


@dataclass
class Contexto:
    """Todo lo que el motor necesita saber de la parcela (entradas 13.2)."""
    clima: list[dict]                 # 12 meses con p, t, tmin, tmax, et0, pe, fr
    altitud: float
    textura: str = "franco"
    ph: float = 6.5
    materia_organica: float = 2.0
    pendiente: float = 5.0
    agua: str = "turnos"
    mes_inicio: int = 9               # 0 = enero
    historial: list[dict] = field(default_factory=list)   # parámetros de cultivos, del más antiguo al más reciente
    problemas: list[str] = field(default_factory=list)
    escenario: str | None = None
    exigir_leguminosa: bool = True

    @property
    def capacidad(self):
        return CAPACIDAD_SUELO.get(self.textura, 75)

    def cobertura_riego(self, mes: int) -> float:
        c = COBERTURA_RIEGO.get(self.agua, 0.5)
        if "falta_agua" in self.problemas and mes in (5, 6, 7, 8):   # verano seco: el riego no alcanza
            c *= 0.5
        return c


# ------------------------------------------------------------------ restricciones esenciales
def _intervalo_ok(fams: list[str], familia: str, minimo: int, n_hist: int, n: int) -> bool:
    """Entre dos cultivos de `familia` debe haber al menos `minimo` ciclos de otras familias,
    tanto en historial + plan como al volver a empezar la rotación (es cíclica)."""
    pos = [i for i, f in enumerate(fams) if f == familia]
    if any(b - a - 1 < minimo for a, b in zip(pos, pos[1:])):
        return False
    en_plan = [p - n_hist for p in pos if p >= n_hist]
    if en_plan and en_plan[0] + n - en_plan[-1] - 1 < minimo:  # hueco al repetir la rotación
        return False
    return True


def restricciones_incumplidas(seq: list[dict], ctx: Contexto) -> list[str]:
    """Devuelve los ids de las restricciones esenciales que la secuencia incumple (vacío = válida)."""
    malas = []
    hist = ctx.historial[-3:]
    ids = [c["id"] for c in hist + seq]
    n_hist, n = len(hist), len(seq)
    for r in REGLAS["restricciones"]:
        t = r["tipo"]
        if t == "mismo_cultivo_consecutivo":
            if any(a == b for a, b in zip(ids, ids[1:])) or (n > 2 and seq[0]["id"] == seq[-1]["id"]):
                malas.append(r["id"])
        elif t == "intervalo_familia":
            minimo = r["ciclos_minimos"] + (1 if r["familia"] == "Solanáceas" and "gusano_blanco" in ctx.problemas else 0)
            fams = [c["familia"] for c in hist + seq]
            if not _intervalo_ok(fams, r["familia"], minimo, n_hist, n):
                malas.append(r["id"])
        elif t == "altitud":
            if any(distancia_altitud(c, ctx.altitud) > r["margen_m"] for c in seq):
                malas.append(r["id"])
        elif t == "aporte_nitrogeno":
            if ctx.exigir_leguminosa and not any(c["n_aporte_kg_ha"] >= r["n_minimo_kg_ha"] for c in seq):
                malas.append(r["id"])
        elif t == "encharcamiento":
            if "encharcamiento" in ctx.problemas and any(c.get("sensible_encharcamiento") for c in seq):
                malas.append(r["id"])
    return malas


def distancia_altitud(c: dict, alt: float) -> float:
    return c["altitud_min"] - alt if alt < c["altitud_min"] else alt - c["altitud_max"] if alt > c["altitud_max"] else 0


# ------------------------------------------------------------------ simulación de un ciclo
def _kc_etapa(kc, k, n):
    r = (k + 0.5) / n
    return kc * 0.7 if r < 0.25 else kc * 0.85 if r > 0.8 else kc * 1.12


def _factor_rotacion(ant, c, esc):
    f = 1.0
    if ant:
        if ant["id"] == c["id"]:
            f *= 0.7
        elif ant["familia"] == c["familia"] and c["familia"] != "Abono verde":
            f *= 0.85
        if ant["n_aporte_kg_ha"] >= 30 and c["n_aporte_kg_ha"] < 30:
            f *= 1.08
        if c["familia"] == "Solanáceas" and ant["familia"] in SAN["rompe_ciclo_papa"]:
            f *= 1.05
    if esc == "lluvioso":
        f *= 0.85 if c["familia"] == "Solanáceas" else 0.92 if c["id"] == "haba" else 1
    return f


def simular_ciclo(c: dict, ant: dict | None, inicio: int, ctx: Contexto) -> dict:
    """Simula un cultivo mes a mes desde el mes absoluto `inicio` (0 = mes de inicio del plan)."""
    m_prev = (ctx.mes_inicio + inicio - 1) % 12
    S = min(ctx.capacidad, 0.5 * ctx.capacidad + ctx.clima[m_prev]["pe"])  # suelo tras el mes de preparación
    need = rain = irr = stress = 0.0
    surv = 1.0
    meses, helada_m, seco_m, linea = [], [], [], []
    for k in range(c["ciclo_meses"]):
        m = (ctx.mes_inicio + inicio + k) % 12
        cl = ctx.clima[m]
        d = _kc_etapa(c["kc"], k, c["ciclo_meses"]) * cl["et0"]
        avail = S + cl["pe"]
        used = min(avail, d)
        deficit = d - used
        S = min(ctx.capacidad, avail - used)
        ir = deficit * ctx.cobertura_riego(m)
        need += d; rain += used; irr += ir; stress += deficit - ir
        if deficit > d * 0.4:
            seco_m.append(m)
        fr = cl["fr"] * (1 - c["tolerancia_helada"] / 3) * 0.35
        if fr > 0.04:
            helada_m.append(m)
        surv *= 1 - fr
        meses.append(m)
        linea.append({"mes": m, "lluvia": cl["p"], "demanda": d, "riego": ir})
    f_alt = clamp(1 - distancia_altitud(c, ctx.altitud) / 500, 0, 1)
    d_ph = c["ph_min"] - ctx.ph if ctx.ph < c["ph_min"] else ctx.ph - c["ph_max"] if ctx.ph > c["ph_max"] else 0
    f_ph = clamp(1 - 0.15 * d_ph, 0.5, 1)
    ky = 1.1 - 0.25 * c["tolerancia_sequia"]
    f_agua = clamp(1 - ky * stress / max(need, 1), 0.15, 1)
    f_helada = max(0.4, surv)
    f_rot = _factor_rotacion(ant, c, ctx.escenario)
    rend = clamp(f_alt * f_ph * f_agua * f_helada * f_rot, 0.05, 1.15)
    residual = ant["n_aporte_kg_ha"] if ant else 0
    oferta_n = min(PARAM["mineralizacion_n_max"], ctx.materia_organica * PARAM["mineralizacion_n_por_mo_pct"]) + residual
    n_aplicar = max(0.0, c["n_demanda_kg_ha"] - oferta_n)
    ingreso = c["rendimiento_t_ha"] * 1000 * rend * c["precio_usd_kg"]
    costo = c["costo_usd_ha"] + n_aplicar * PARAM["precio_n_usd_kg"]
    return {"cultivo": c, "anterior": ant, "inicio": inicio, "fin": inicio + c["ciclo_meses"] - 1,
            "demanda": need, "lluvia": rain, "riego": irr, "deficit": stress,
            "f_alt": f_alt, "f_ph": f_ph, "f_agua": f_agua, "f_helada": f_helada, "f_rot": f_rot,
            "rendimiento_rel": rend, "perdida_clima": 1 - f_alt * f_agua * f_helada,
            "n_residual": residual, "n_aplicar": n_aplicar, "ahorro_n": min(residual, c["n_demanda_kg_ha"]) * PARAM["precio_n_usd_kg"],
            "ingreso": ingreso, "costo": costo, "margen": ingreso - costo,
            "meses_helada": helada_m, "meses_secos": seco_m, "linea": linea}


# ------------------------------------------------------------------ puntuación
def sanidad(seq: list[dict], ctx: Contexto) -> float:
    s = 100.0
    n = len(seq)
    prev = ctx.historial[-1] if ctx.historial else None

    def par(a, b, w):
        nonlocal s
        if not a or not b:
            return
        p = 0
        if a["id"] == b["id"]:
            p = SAN["mismo_cultivo"] + (15 if a["familia"] == "Solanáceas" else 0)
        elif a["familia"] == b["familia"] and a["familia"] != "Abono verde":
            p = SAN["misma_familia"].get(a["familia"], SAN["misma_familia"]["otras"])
        s -= p * w
        if b["familia"] == "Solanáceas" and (a["familia"] in SAN["rompe_ciclo_papa"] or a["id"] == "chocho"):
            s += SAN["bonificacion_rompe_ciclo_papa"] * w

    def gap(a, b):
        nonlocal s
        if a and b and a["familia"] == b["familia"]:
            s -= SAN["familia_a_dos_ciclos"].get(a["familia"], 0)

    if prev:
        par(prev, seq[0], 1)
        if n > 1:
            gap(prev, seq[1])
    for i in range(1, n):
        par(seq[i - 1], seq[i], 1)
    if n > 2:
        par(seq[-1], seq[0], 0.5)
    if n == 4:
        gap(seq[0], seq[2]); gap(seq[1], seq[3])
    ids = [c["id"] for c in seq]
    s -= SAN.get("cultivo_repetido_en_rotacion", 0) * (len(ids) - len(set(ids)))  # menos diversidad
    if ctx.escenario == "lluvioso":
        s -= sum(8 for c in seq if c["familia"] == "Solanáceas") + sum(4 for c in seq if c["id"] == "haba")
    return clamp(s, 0, 100)


def puntuar(seq: list[dict], ciclos: list[dict], ctx: Contexto, pesos: dict, prep: int | None = None) -> dict:
    n = len(seq)
    prep = PARAM["mes_preparacion_entre_cultivos"] if prep is None else prep
    meses = sum(c["ciclo_meses"] for c in seq) + (n - 1) * prep
    diversidad = len({c["familia"] for c in seq}) / n
    dem = sum(c["n_demanda_kg_ha"] for c in seq)
    fij = sum(c["n_aporte_kg_ha"] for c in seq)
    ratio_n = clamp(fij / (0.3 * dem + 1), 0, 1)
    residuos = sum(c["residuos"] / 3 for c in seq) / n
    factor_pend = 0.4 + ctx.pendiente / 25
    if "erosion" in ctx.problemas:
        factor_pend *= 1.3
    erosion = clamp(sum((c["laboreo"] / 3) * 0.6 + (1 - c["cobertura"] / 3) * 0.4 for c in seq) / n * factor_pend, 0, 1)
    need = sum(x["demanda"] for x in ciclos)
    rain = sum(x["lluvia"] for x in ciclos)
    margen = sum(x["margen"] for x in ciclos)
    margen_anual = margen / (meses / 12)
    sc = {
        "suelo": 100 * (0.25 * diversidad + 0.25 * ratio_n + 0.2 * residuos + 0.3 * (1 - erosion)),
        "agua": 100 * clamp(rain / max(need, 1), 0, 1),
        "clima": 100 * clamp(1 - 1.6 * sum(x["perdida_clima"] for x in ciclos) / n, 0, 1),
        "sanidad": sanidad(seq, ctx),
        "ingresos": clamp(50 + margen_anual / 60, 0, 100),  # 3000 USD/ha/año = 100
    }
    wsum = sum(pesos.get(k, 0) for k in CRITERIOS) or 1
    total = sum(sc[k] * pesos.get(k, 0) for k in CRITERIOS) / wsum
    return {"puntajes": sc, "total": total, "meses": meses, "margen_anual": margen_anual,
            "riego_total": sum(x["riego"] for x in ciclos), "deficit_total": sum(x["deficit"] for x in ciclos),
            "ahorro_n": sum(x["ahorro_n"] for x in ciclos), "erosion": erosion, "diversidad": diversidad,
            "demanda_total": need, "lluvia_usada": rain}


# ------------------------------------------------------------------ búsqueda
def candidatos(cultivos: list[dict], ctx: Contexto) -> tuple[list[dict], list[dict]]:
    margen = next(r["margen_m"] for r in REGLAS["restricciones"] if r["tipo"] == "altitud")
    ok = [c for c in cultivos if distancia_altitud(c, ctx.altitud) <= margen]
    return ok, [c for c in cultivos if c not in ok]


def evaluar_secuencia(seq: list[dict], ctx: Contexto, pesos: dict, cache: dict | None = None, prep: int | None = None) -> dict:
    cache = {} if cache is None else cache
    prep = PARAM["mes_preparacion_entre_cultivos"] if prep is None else prep
    ciclos, t = [], 0
    prev = ctx.historial[-1] if ctx.historial else None
    for i, c in enumerate(seq):
        if i > 0:
            t += prep
        ant = prev if i == 0 else seq[i - 1]
        key = (c["id"], c["ciclo_meses"], t, ant["id"] if ant else None)
        if key not in cache:
            cache[key] = simular_ciclo(c, ant, t, ctx)
        ciclos.append(cache[key])
        t += c["ciclo_meses"]
    res = puntuar(seq, ciclos, ctx, pesos, prep)
    res.update({"secuencia": seq, "ciclos": ciclos, "restricciones_incumplidas": restricciones_incumplidas(seq, ctx)})
    return res


def optimizar(cultivos: list[dict], ctx: Contexto, pesos: dict, n: int = 4, top: int = 3) -> dict:
    """Prueba todas las secuencias válidas de n cultivos y devuelve las `top` mejores y diferentes."""
    cand, excluidos = candidatos(cultivos, ctx)
    cache: dict = {}
    validas = []
    descartadas = 0
    for seq in itertools.product(cand, repeat=n):
        seq = list(seq)
        if any(a["id"] == b["id"] for a, b in zip(seq, seq[1:])):
            descartadas += 1
            continue
        if restricciones_incumplidas(seq, ctx):
            descartadas += 1
            continue
        validas.append(evaluar_secuencia(seq, ctx, pesos, cache))
    validas.sort(key=lambda r: -r["total"])
    elegidas = []
    min_dif = 2 if n >= 4 else 1
    for r in validas:
        if all(_diferencia(p["secuencia"], r["secuencia"]) >= min_dif for p in elegidas):
            elegidas.append(r)
        if len(elegidas) == top:
            break
    return {"alternativas": elegidas, "evaluadas": len(validas), "descartadas": descartadas,
            "candidatos": cand, "excluidos_altitud": excluidos}


def _diferencia(a, b):
    resto = [c["id"] for c in a]
    comunes = 0
    for c in b:
        if c["id"] in resto:
            resto.remove(c["id"]); comunes += 1
    return len(a) - comunes


# ------------------------------------------------------------------ plan anual (12 meses, 3 etapas)
PLAN_ANUAL = REGLAS["plan_anual"]
ETAPAS = PLAN_ANUAL["etapas"]


def variante_anual(c: dict, etapa: dict, altitud: float) -> dict | None:
    """Versión de ciclo corto de un cultivo para una etapa del plan anual (None si no cabe en esa etapa)."""
    cfg = (c.get("anual") or {}).get(str(etapa["n"]))
    if not cfg or (cfg.get("alt_max") and altitud > cfg["alt_max"]):
        return None
    return c | {"ciclo_meses": etapa["meses"], "rendimiento_t_ha": c["rendimiento_t_ha"] * cfg["rend"],
                "costo_usd_ha": c["costo_usd_ha"] * cfg["costo"], "uso_anual": cfg["uso"], "etapa": etapa["n"],
                "etapa_nombre": etapa["nombre"], "etapa_rol": etapa["rol"]}


def optimizar_anual(cultivos: list[dict], ctx: Contexto, pesos: dict, top: int = 3) -> dict:
    """Plan de 12 meses: un cultivo por etapa (lluvias 5 m, salida de lluvias 4 m, verano 3 m), sin meses de descanso."""
    cand, excluidos = candidatos(cultivos, ctx)
    por_etapa = [[v for c in cand if (v := variante_anual(c, e, ctx.altitud))] for e in ETAPAS]
    cache: dict = {}
    validas, descartadas = [], 0
    for seq in itertools.product(*por_etapa):
        seq = list(seq)
        if restricciones_incumplidas(seq, ctx):
            descartadas += 1
            continue
        validas.append(evaluar_secuencia(seq, ctx, pesos, cache, prep=0))
    validas.sort(key=lambda r: -r["total"])
    elegidas = []
    for r in validas:
        if all(_diferencia(p["secuencia"], r["secuencia"]) >= 1 for p in elegidas):
            elegidas.append(r)
        if len(elegidas) == top:
            break
    sin_etapa = [e["nombre"] for e, lista in zip(ETAPAS, por_etapa) if not lista]
    return {"alternativas": elegidas, "evaluadas": len(validas), "descartadas": descartadas, "candidatos": cand,
            "excluidos_altitud": excluidos, "etapas_sin_cultivo": sin_etapa}
