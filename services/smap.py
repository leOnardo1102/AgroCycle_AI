"""NASA SMAP L3/L4 (9–36 km) - humedad superficial del suelo y anomalía hídrica.

Estima la humedad volumétrica superficial y radicular normalizada (0-1) para Chimborazo
con respaldo offline en data/nasa_respaldo_chimborazo.json, detectando déficit o exceso
hídrico respecto a la normal climatológica para alimentar el simulador de escenarios.
"""
import json
from datetime import date

from config import LAT_CHIMBORAZO, LON_CHIMBORAZO, RESPALDO_NASA
from utils.calculos import MESES_L, clamp

_SMAP_BASE = {
    "humedad_mensual": [0.62, 0.68, 0.74, 0.76, 0.65, 0.48, 0.31, 0.25, 0.29, 0.54, 0.60, 0.61],
    "humedad_normal": 0.54,
}


def _cargar_base() -> dict:
    if RESPALDO_NASA.exists():
        try:
            data = json.loads(RESPALDO_NASA.read_text(encoding="utf-8")).get("smap")
            if isinstance(data, dict) and len(data.get("humedad_mensual", [])) == 12:
                return data
        except (ValueError, OSError):
            pass
    return dict(_SMAP_BASE)


def reconstruir_desde_curva(
    humedad_mensual: list[float],
    humedad_normal: float | None = None,
    mes_actual: int | None = None,
    fuente: str = "NASA SMAP L4 (climatología Chimborazo)",
) -> dict:
    """Construye el diagnóstico de humedad superficial SMAP y su anomalía hídrica."""
    serie = [round(clamp(float(v), 0.10, 0.95), 3) for v in humedad_mensual[:12]]
    if len(serie) < 12:
        serie = (serie + list(_SMAP_BASE["humedad_mensual"]))[:12]

    idx_actual = (date.today().month - 1) if mes_actual is None else int(mes_actual) % 12
    normal = round(float(humedad_normal if humedad_normal is not None else sum(serie) / 12), 3)
    sup = serie[idx_actual]
    rad = round(clamp(0.65 * sup + 0.35 * normal, 0.12, 0.95), 3)
    anomalia_pct = round(((sup - normal) / max(normal, 0.05)) * 100.0, 1)

    if anomalia_pct < -8.0:
        estado = "deficit"
        escenario_sugerido = "seco"
    elif anomalia_pct > 12.0:
        estado = "exceso"
        escenario_sugerido = "lluvioso"
    else:
        estado = "normal"
        escenario_sugerido = "normal"

    meses_deficit = [i for i, v in enumerate(serie) if v < 0.40]
    nombres_deficit = [MESES_L[i] for i in meses_deficit]
    factor_agua = round(clamp(sup / max(normal, 0.10), 0.70, 1.30), 2)

    return {
        "fuente": fuente,
        "resolucion": "9–36 km",
        "humedad_mensual": serie,
        "humedad_superficial": sup,
        "humedad_superficial_pct": round(sup * 100, 1),
        "humedad_radicular": rad,
        "humedad_normal": normal,
        "anomalia_hidrica_pct": anomalia_pct,
        "estado_hidrico": estado,
        "mes_actual": idx_actual,
        "meses_deficit": meses_deficit,
        "meses_deficit_nombres": nombres_deficit,
        "escenario_sugerido": escenario_sugerido,
        "factor_agua_inicial": factor_agua,
    }


def consultar(
    lat: float,
    lon: float,
    mes_actual: int | None = None,
    lluvia_mensual: list[float] | None = None,
) -> dict:
    """Estima la humedad superficial del suelo (NASA SMAP) y su anomalía hídrica para la parcela."""
    base = _cargar_base()
    serie_base = base["humedad_mensual"]
    normal_base = float(base.get("humedad_normal", sum(serie_base) / 12))

    # Ajuste espacial leve por posición en Chimborazo y lluvia local si está disponible
    delta_geo = clamp(-0.04 * (lon - LON_CHIMBORAZO) + 0.02 * (lat - LAT_CHIMBORAZO), -0.05, 0.05)
    serie = []
    for i, val in enumerate(serie_base):
        delta_lluvia = 0.0
        if lluvia_mensual and len(lluvia_mensual) == 12:
            delta_lluvia = clamp((lluvia_mensual[i] - 95.0) / 1200.0, -0.08, 0.08)
        serie.append(round(clamp(val + delta_geo + delta_lluvia, 0.12, 0.92), 3))

    return reconstruir_desde_curva(serie, humedad_normal=normal_base, mes_actual=mes_actual)
