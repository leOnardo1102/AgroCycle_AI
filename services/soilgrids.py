"""SoilGrids (ISRIC) - propiedades estimadas del suelo a 250 m. Fuente complementaria (sección 16, mitigación).

Por qué no basta con la API REST «properties/query»:
  1. La API REST de ISRIC está en beta y a menudo responde 503 o no responde (tiempo agotado).
  2. SoilGrids no tiene datos en zonas urbanas, cuerpos de agua y algunas celdas de páramo. Los centros de
     Riobamba, Guano, Chambo, Guamote, Alausí y Chunchi caen en celdas sin dato, así que muchas parcelas
     cercanas a los poblados quedaban sin suelo.

Solución:
  - Fuente principal: el servicio WCS de ISRIC (maps.isric.org), más estable. Se pide una ventana pequeña
    alrededor de la parcela para cada propiedad y profundidad (en paralelo) y se usa la celda válida más cercana
    al punto (si la del punto no tiene dato, la vecina de 250 m es representativa). Si en ~700 m no hay celdas
    válidas, se amplía la búsqueda a ~3 km.
  - Respaldo: la API REST (si el WCS no respondió).
  - Si ambas fallan, datos_ambientales usa la referencia SoilGrids del cantón (data/soilgrids_cantones.json).
"""
import io
from concurrent.futures import ThreadPoolExecutor

import requests

from config import TIMEOUT_SOILGRIDS_S
from services import ServicioNoDisponible
from utils.calculos import distancia_km, textura_usda

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
URL_WCS = "https://maps.isric.org/mapserv?map=/map/{prop}.map"
PROPIEDADES = ("phh2o", "soc", "sand", "clay")
PROFUNDIDADES = (("0-5cm", 5), ("5-15cm", 10), ("15-30cm", 15))  # (capa, espesor en cm) -> media ponderada 0-30 cm
VENTANAS_GRADOS = (0.006, 0.03)  # medio lado de la ventana de búsqueda: ~670 m y ~3,3 km
CRS_4326 = "http://www.opengis.net/def/crs/EPSG/0/4326"


# ------------------------------------------------------------------ interpretación
def _resultado(ph, soc, arena, arcilla, fuente="SoilGrids", **extra) -> dict:
    """ph en unidades de pH, soc en g/kg, arena y arcilla en %."""
    return {"fuente": fuente, "ph": round(ph, 1),
            "materia_organica": round(soc * 1.724 / 10, 1) if soc is not None else None,
            "arena": round(arena) if arena is not None else None,
            "arcilla": round(arcilla) if arcilla is not None else None,
            "textura": textura_usda(arena, arcilla) if arena is not None and arcilla is not None else None,
            **extra}


def interpretar(j: dict) -> dict:
    """Respuesta de la API REST «properties/query»."""
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
    return _resultado(vals["phh2o"], vals.get("soc"), vals.get("sand"), vals.get("clay"))


def _valido(v) -> bool:
    """En el WCS las celdas sin dato llegan como 0 o -32768 (ninguna propiedad usada puede valer 0 de verdad)."""
    return v is not None and v > 0 and v != 32767


def combinar_rejillas(rejillas: dict, lat: float, lon: float, media_lado: float) -> dict:
    """rejillas[(prop, capa)] = matriz [filas][columnas] de enteros SoilGrids (factor 10) de una ventana centrada en
    (lat, lon) con medio lado `media_lado` grados. Devuelve el suelo de la celda válida más cercana al punto."""
    base = rejillas[("phh2o", PROFUNDIDADES[0][0])]
    filas, cols = len(base), len(base[0]) if base else 0
    if not filas or not cols:
        raise ServicioNoDisponible("SoilGrids devolvió una ventana vacía")
    esp_total = sum(e for _, e in PROFUNDIDADES)
    mejor = None
    for y in range(filas):
        for x in range(cols):
            vals = {}
            for prop in PROPIEDADES:
                capas = [(rejillas.get((prop, c)), e) for c, e in PROFUNDIDADES]
                datos = [(m[y][x], e) for m, e in capas if m is not None and y < len(m) and x < len(m[y]) and _valido(m[y][x])]
                if len(datos) == len(PROFUNDIDADES):
                    vals[prop] = sum(v * e for v, e in datos) / esp_total / 10
            if "phh2o" not in vals:
                continue
            la = lat + media_lado - (y + 0.5) * 2 * media_lado / filas
            lo = lon - media_lado + (x + 0.5) * 2 * media_lado / cols
            dist = distancia_km(lat, lon, la, lo) * 1000
            if mejor is None or dist < mejor[0]:
                mejor = (dist, vals)
    if mejor is None:
        raise ServicioNoDisponible("SoilGrids sin datos en este punto (zona urbana, agua o fuera de cobertura)")
    dist, v = mejor
    return _resultado(v["phh2o"], v.get("soc"), v.get("sand"), v.get("clay"), distancia_m=round(dist))


# ------------------------------------------------------------------ consultas
def _leer_tiff(contenido: bytes) -> list[list[int]]:
    from PIL import Image  # Pillow ya viene con Streamlit
    im = Image.open(io.BytesIO(contenido))
    w, h = im.size
    px = im.load()
    return [[px[x, y] for x in range(w)] for y in range(h)]


def _rejilla_wcs(prop: str, capa: str, lat: float, lon: float, media_lado: float, timeout: float) -> list[list[int]]:
    params = {"SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCoverage", "COVERAGEID": f"{prop}_{capa}_mean",
              "FORMAT": "image/tiff", "SUBSETTINGCRS": CRS_4326, "OUTPUTCRS": CRS_4326,
              "SUBSET": [f"long({lon - media_lado:.6f},{lon + media_lado:.6f})", f"lat({lat - media_lado:.6f},{lat + media_lado:.6f})"]}
    t_req = min(timeout, 8)
    try:
        r = requests.get(URL_WCS.format(prop=prop), params=params, timeout=t_req)
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image"):
            raise ServicioNoDisponible("SoilGrids WCS devolvió un error en lugar de la imagen")
        return _leer_tiff(r.content)
    except (requests.RequestException, OSError, ServicioNoDisponible) as e:
        raise ServicioNoDisponible(f"SoilGrids no respondió ({type(e).__name__})") from e


def consultar_wcs(lat: float, lon: float, timeout: float = TIMEOUT_SOILGRIDS_S) -> dict:
    piezas = [(p, c) for p in PROPIEDADES for c, _ in PROFUNDIDADES]
    error_sin_dato = None
    with ThreadPoolExecutor(max_workers=len(piezas)) as ex:
        for media_lado in VENTANAS_GRADOS:
            futuros = {k: ex.submit(_rejilla_wcs, *k, lat, lon, media_lado, timeout) for k in piezas}
            rejillas = {k: f.result() for k, f in futuros.items()}  # propaga ServicioNoDisponible si no responde
            try:
                return combinar_rejillas(rejillas, lat, lon, media_lado)
            except ServicioNoDisponible as e:
                error_sin_dato = e  # sin celdas válidas: se amplía la ventana
    raise error_sin_dato


def consultar_rest(lat: float, lon: float, timeout: float = TIMEOUT_SOILGRIDS_S) -> dict:
    params = [("lon", lon), ("lat", lat), ("value", "mean")] + \
             [("property", p) for p in PROPIEDADES] + \
             [("depth", d) for d, _ in PROFUNDIDADES]
    try:
        r = requests.get(URL, params=params, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise ServicioNoDisponible(f"SoilGrids no respondió ({type(e).__name__})") from e
    return interpretar(r.json())


def consultar(lat: float, lon: float, timeout: float = TIMEOUT_SOILGRIDS_S) -> dict:
    """Suelo 0-30 cm de la parcela: WCS de ISRIC (con búsqueda de la celda válida más cercana) y, si no responde, API REST."""
    try:
        return consultar_wcs(lat, lon, timeout)
    except ServicioNoDisponible as e_wcs:
        if "sin datos" in str(e_wcs):
            raise  # la API REST usa la misma cuadrícula: tampoco tendría datos
        try:
            return consultar_rest(lat, lon, min(timeout, 8))
        except ServicioNoDisponible:
            raise e_wcs from None
