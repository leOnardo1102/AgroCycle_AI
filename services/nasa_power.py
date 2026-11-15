"""NASA POWER - climatología mensual para agricultura (prioridad 1, sección 11.1).
Documentación: https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
"""
import requests

from config import TIMEOUT_NASA_S
from services import ServicioNoDisponible

URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
PARAMETROS = "T2M,T2M_MIN,T2M_MAX,PRECTOTCORR,ALLSKY_SFC_SW_DWN,GWETROOT"
PARAMETROS_MINIMOS = "T2M,T2M_MIN,T2M_MAX,PRECTOTCORR"  # si NASA rechaza alguno de los opcionales
MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DIAS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def url_consulta(lat: float, lon: float, parametros: str = PARAMETROS) -> str:
    return f"{URL}?parameters={parametros}&community=AG&longitude={lon}&latitude={lat}&format=JSON"


def interpretar(j: dict) -> dict:
    """Convierte la respuesta JSON de NASA POWER en 12 meses de clima."""
    try:
        p = j["properties"]["parameter"]
        pr, t = p.get("PRECTOTCORR") or p["PRECTOT"], p["T2M"]
        tn, tx, rad, gw = p.get("T2M_MIN"), p.get("T2M_MAX"), p.get("ALLSKY_SFC_SW_DWN"), p.get("GWETROOT")
        meses = []
        for i, k in enumerate(MESES):
            if pr[k] is None or pr[k] <= -990 or t[k] <= -990:
                raise ServicioNoDisponible("NASA POWER devolvió meses sin datos (-999)")
            meses.append({"p": round(pr[k] * DIAS[i], 1),  # mm/día -> mm/mes
                          "t": t[k],
                          "tmin": tn[k] if tn and tn[k] > -990 else t[k] - 6.2,
                          "tmax": tx[k] if tx and tx[k] > -990 else t[k] + 6.8,
                          "rad": rad[k] if rad and rad[k] is not None and rad[k] > -990 else None,   # kWh/m²/día
                          "gwetroot": gw[k] if gw and gw[k] is not None and gw[k] > -990 else None})  # humedad radicular 0-1
        coords = j.get("geometry", {}).get("coordinates", [])
        return {"fuente": "NASA POWER", "elev_celda": coords[2] if len(coords) > 2 else None, "meses": meses}
    except (KeyError, TypeError) as e:
        raise ServicioNoDisponible(f"Formato inesperado de NASA POWER: {e}") from e


def consultar(lat: float, lon: float, timeout: float = TIMEOUT_NASA_S) -> dict:
    try:
        r = requests.get(url_consulta(lat, lon), timeout=timeout)
        if r.status_code == 422:  # algún parámetro opcional no disponible: pedir solo lo esencial
            r = requests.get(url_consulta(lat, lon, PARAMETROS_MINIMOS), timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise ServicioNoDisponible(f"NASA POWER no respondió ({type(e).__name__})") from e
    return interpretar(r.json())
