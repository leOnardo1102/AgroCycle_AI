"""NASA SRTM 30 m - altitud, pendiente y riesgo de erosión en ladera vía OpenTopoData."""
import math

import requests

from config import TIMEOUT_SRTM_S
from services import ServicioNoDisponible
from utils.calculos import pendiente_pct

URL = "https://api.opentopodata.org/v1/srtm30m"


def evaluar_erosion_ladera(pendiente: float) -> dict:
    """Calcula el nivel de riesgo de erosión en ladera y la práctica de conservación recomendada."""
    p = max(0.0, float(pendiente))
    # Factor topográfico LS simplificado (RUSLE) para ladera típica de 40 m en sierra andina
    angulo = math.atan(p / 100.0)
    factor_ls = round((40.0 / 22.13) ** 0.4 * (65.41 * math.sin(angulo) ** 2 + 4.56 * math.sin(angulo) + 0.065), 2)

    if p < 5.0:
        riesgo = "bajo"
        clase = "Terreno plano a casi plano (< 5 %)"
        recomendacion = "Labranza mínima conservando rastrojos en superficie."
    elif p < 12.0:
        riesgo = "moderado"
        clase = "Pendiente suave (5–12 %)"
        recomendacion = "Surcos en contorno y rotación con cultivos de buena cobertura."
    elif p < 25.0:
        riesgo = "alto"
        clase = "Ladera inclinada (12–25 %)"
        recomendacion = "Curvas de nivel obligatorias, zanjas de desviación y barreras vivas (sigse/pasto)."
    else:
        riesgo = "muy_alto"
        clase = "Ladera escarpada (>= 25 %)"
        recomendacion = "Evitar cultivos de laboreo intenso; priorizar pradera permanente, pastos o cobertura densa."

    return {
        "riesgo_erosion_ladera": riesgo,
        "clase_relieve": clase,
        "factor_ls": factor_ls,
        "recomendacion_ladera": recomendacion,
    }


def consultar(lat: float, lon: float, paso_m: float = 60.0, timeout: float = TIMEOUT_SRTM_S) -> dict:
    dlat = paso_m / 111_320
    dlon = paso_m / (111_320 * math.cos(math.radians(lat)))
    pts = [(lat, lon), (lat + dlat, lon), (lat - dlat, lon), (lat, lon + dlon), (lat, lon - dlon)]
    try:
        r = requests.get(URL, params={"locations": "|".join(f"{a:.6f},{b:.6f}" for a, b in pts)}, timeout=timeout)
        r.raise_for_status()
        elevs = [x["elevation"] for x in r.json()["results"]]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise ServicioNoDisponible(f"SRTM no respondió ({type(e).__name__})") from e
    if any(e is None for e in elevs):
        raise ServicioNoDisponible("SRTM sin datos en este punto")
    pend = pendiente_pct(elevs, paso_m)
    return {
        "fuente": "NASA SRTM",
        "elevacion": round(elevs[0]),
        "pendiente": pend,
        **evaluar_erosion_ladera(pend),
    }
