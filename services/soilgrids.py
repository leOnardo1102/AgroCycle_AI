"""SoilGrids (ISRIC) - propiedades estimadas del suelo a 250 m. Fuente complementaria (sección 16, mitigación)."""
import requests

from config import TIMEOUT_SOILGRIDS_S
from services import ServicioNoDisponible
from utils.calculos import textura_usda

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"


def interpretar(j: dict) -> dict:
    vals = {}
    try:
        for capa in j["properties"]["layers"]:
            d = capa.get("unit_measure", {}).get("d_factor", 10) or 10
            medias = [x["values"].get("mean") for x in capa["depths"] if x["values"].get("mean") is not None]
            if medias:
                vals[capa["name"]] = sum(medias) / len(medias) / d
    except (KeyError, TypeError) as e:
        raise ServicioNoDisponible(f"Formato inesperado de SoilGrids: {e}") from e
    if "phh2o" not in vals:
        raise ServicioNoDisponible("SoilGrids sin datos en este punto")
    arena, arcilla, soc = vals.get("sand"), vals.get("clay"), vals.get("soc")  # %, %, g/kg
    return {"fuente": "SoilGrids", "ph": round(vals["phh2o"], 1),
            "materia_organica": round(soc * 1.724 / 10, 1) if soc is not None else None,
            "arena": round(arena) if arena is not None else None,
            "arcilla": round(arcilla) if arcilla is not None else None,
            "textura": textura_usda(arena, arcilla) if arena is not None and arcilla is not None else None}


def consultar(lat: float, lon: float, timeout: float = TIMEOUT_SOILGRIDS_S) -> dict:
    params = [("lon", lon), ("lat", lat), ("value", "mean")] + \
             [("property", p) for p in ("phh2o", "soc", "sand", "clay")] + \
             [("depth", d) for d in ("0-5cm", "5-15cm", "15-30cm")]
    try:
        r = requests.get(URL, params=params, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise ServicioNoDisponible(f"SoilGrids no respondió ({type(e).__name__})") from e
    return interpretar(r.json())
