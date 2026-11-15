"""Cálculos agroclimáticos y geográficos usados por el motor (sin dependencias externas)."""
import math

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_L = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
           "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# Patrón bimodal de lluvia del callejón interandino (% del total anual)
PATRON_LLUVIA = [8, 9, 12, 13, 9, 6, 4, 3, 5, 10, 11, 10]
T_OFFSET = [0.2, 0.2, 0.2, 0.3, 0.2, -0.2, -0.4, -0.3, 0.1, 0.3, 0.4, 0.3]
TMIN_OFFSET = [0, 0, 0.2, 0.4, 0.2, -0.6, -1.2, -1.4, -0.6, 0, 0, -0.3]
# Radiación extraterrestre aprox. a ~1.8° S (MJ m-2 d-1)
RA = [37.5, 37.9, 37.6, 36.0, 34.2, 33.1, 33.5, 35.1, 36.8, 37.6, 37.4, 37.1]
QUINTAL_KG = 45.36


def clamp(x, a, b):
    return max(a, min(b, x))


def et0_hargreaves(mes: int, t: float, tmin: float, tmax: float) -> float:
    """Evapotranspiración de referencia mensual (mm). Hargreaves calibrado x0.85 para la sierra."""
    return 0.85 * 0.0023 * RA[mes] * 0.408 * (t + 17.8) * math.sqrt(max(tmax - tmin, 1)) * DIAS[mes]


def lluvia_efectiva(p: float) -> float:
    """Lluvia efectiva mensual, método USDA-SCS (el que usa CROPWAT de FAO)."""
    return p * (125 - 0.2 * p) / 125 if p <= 250 else 125 + 0.1 * p


def riesgo_helada(tmin: float, desviacion: float = 2.5) -> float:
    """Índice (0-1) de riesgo de helada del mes. Supone que la mínima diaria sigue una normal
    alrededor de la mínima media mensual (desviación ~2,5 °C) y escala la probabilidad de una
    noche bajo 0 °C (x4) para representar el riesgo de varias noches de helada en el mes."""
    p_noche = 0.5 * (1 + math.erf((0 - tmin) / (desviacion * math.sqrt(2))))
    return clamp(p_noche * 4, 0, 1)


def clima_estimado(altitud: float, lluvia_anual: float) -> list[dict]:
    """Clima mensual de referencia por gradiente altitudinal (respaldo cuando NASA POWER no responde)."""
    tm = 13.8 - 0.0058 * (altitud - 2750)
    out = []
    for i in range(12):
        t = tm + T_OFFSET[i]
        out.append({"p": lluvia_anual * PATRON_LLUVIA[i] / 100, "t": t,
                    "tmin": t - 6.2 + TMIN_OFFSET[i], "tmax": t + 6.8 - TMIN_OFFSET[i] * 0.5})
    return out


def completar_clima(meses: list[dict]) -> list[dict]:
    """Agrega ET0, lluvia efectiva y riesgo de helada a cada mes."""
    return [{**m, "et0": et0_hargreaves(i, m["t"], m["tmin"], m["tmax"]),
             "pe": lluvia_efectiva(m["p"]), "fr": riesgo_helada(m["tmin"])} for i, m in enumerate(meses)]


def distancia_km(lat1, lon1, lat2, lon2) -> float:
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return math.hypot(x, y) * 6371


def area_poligono_ha(coords: list[list[float]]) -> float:
    """Área geodésica aproximada de un polígono [[lon, lat], ...] en hectáreas."""
    if not coords or len(coords) < 3:
        return 0.0
    r = math.pi / 180
    a = 0.0
    for i in range(len(coords)):
        lon1, lat1 = coords[i][:2]
        lon2, lat2 = coords[(i + 1) % len(coords)][:2]
        a += (lon2 - lon1) * r * (2 + math.sin(lat1 * r) + math.sin(lat2 * r))
    return abs(a * 6378137 ** 2 / 2) / 10000


def pendiente_pct(elevs: list[float], paso_m: float) -> float:
    """elevs = [centro, norte, sur, este, oeste] -> pendiente en %."""
    _, n, s, e, o = elevs
    return round(math.hypot((e - o) / (2 * paso_m), (n - s) / (2 * paso_m)) * 100, 1)


def textura_usda(arena: float, arcilla: float) -> str:
    if arena >= 70:
        return "arenoso"
    if arcilla >= 40:
        return "arcilloso"
    if arcilla >= 27:
        return "francoarcilloso"
    if arena >= 50 and arcilla < 20:
        return "francoarenoso"
    return "franco"
