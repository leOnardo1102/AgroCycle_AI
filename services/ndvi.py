"""NDVI (MODIS / Landsat / Sentinel-2) - cobertura vegetal y detección de suelo desnudo para Chimborazo.

Combina la climatología estacional de vegetación calibrada para el callejón interandino con
respaldo offline en data/nasa_respaldo_chimborazo.json, acotada entre 0,15 (suelo desnudo) y
0,85 (vegetación densa), para detectar ventanas críticas de suelo descubierto (ej. julio-septiembre).
"""
import json
import math
from datetime import date

from config import LAT_CHIMBORAZO, LON_CHIMBORAZO, RESPALDO_NASA
from utils.calculos import MESES_L, clamp

MIN_NDVI = 0.15
MAX_NDVI = 0.85
UMBRAL_SUELO_DESNUDO = 0.30
UMBRAL_VEGETACION_DENSA = 0.68

_CURVA_BASE_CHIMBORAZO = [0.58, 0.65, 0.74, 0.78, 0.66, 0.45, 0.24, 0.19, 0.23, 0.46, 0.55, 0.57]


def _cargar_curva_respaldo() -> list[float]:
    if RESPALDO_NASA.exists():
        try:
            data = json.loads(RESPALDO_NASA.read_text(encoding="utf-8"))
            curva = data.get("ndvi_mensual")
            if isinstance(curva, list) and len(curva) == 12:
                return [float(x) for x in curva]
        except (ValueError, OSError):
            pass
    return list(_CURVA_BASE_CHIMBORAZO)


def clasificar_ndvi(valor: float) -> str:
    """Clasifica un valor NDVI en estado de cobertura del suelo."""
    if valor <= UMBRAL_SUELO_DESNUDO:
        return "suelo_desnudo"
    if valor <= 0.50:
        return "cobertura_baja"
    if valor <= UMBRAL_VEGETACION_DENSA:
        return "cobertura_media"
    return "vegetacion_densa"


def reconstruir_desde_curva(
    curva: list[float],
    ndvi_actual: float | None = None,
    fuente: str = "NASA MODIS / Landsat / Sentinel-2",
    mes_actual: int | None = None,
) -> dict:
    """Construye el diagnóstico completo de NDVI a partir de una serie de 12 meses."""
    serie = [round(clamp(float(v), MIN_NDVI, MAX_NDVI), 3) for v in curva[:12]]
    if len(serie) < 12:
        serie = (serie + list(_CURVA_BASE_CHIMBORAZO))[:12]

    idx_actual = (date.today().month - 1) if mes_actual is None else int(mes_actual) % 12
    actual = round(clamp(float(ndvi_actual if ndvi_actual is not None else serie[idx_actual]), MIN_NDVI, MAX_NDVI), 3)
    promedio = round(sum(serie) / 12, 3)
    vmin = min(serie)
    vmax = max(serie)
    meses_desnudos = [i for i, v in enumerate(serie) if v <= UMBRAL_SUELO_DESNUDO]
    nombres_criticos = [MESES_L[i] for i in meses_desnudos]

    if len(meses_desnudos) >= 3 or vmin <= 0.22:
        riesgo = "alto"
    elif len(meses_desnudos) >= 1:
        riesgo = "medio"
    else:
        riesgo = "bajo"

    if meses_desnudos:
        meses_txt = ", ".join(nombres_criticos)
        alerta = (
            f"Suelo desnudo crítico en {meses_txt} (NDVI <= {UMBRAL_SUELO_DESNUDO:.2f}): "
            "riesgo de erosión eólica e hídrica; requiere cultivo de cobertura o rastrojo."
        )
    else:
        alerta = "Cobertura vegetal estable durante el año sin meses críticos de suelo desnudo."

    return {
        "fuente": fuente,
        "resolucion": "30–250 m",
        "ndvi_promedio": promedio,
        "ndvi_actual": actual,
        "ndvi_min": vmin,
        "ndvi_max": vmax,
        "curva_estacional": serie,
        "meses": serie,
        "mes_actual": idx_actual,
        "meses_suelo_desnudo": meses_desnudos,
        "meses_criticos_nombres": nombres_criticos,
        "riesgo_erosion_ndvi": riesgo,
        "estado_actual": clasificar_ndvi(actual),
        "alerta_erosion": alerta,
    }


def consultar(
    lat: float,
    lon: float,
    mes_actual: int | None = None,
    lluvia_mensual: list[float] | None = None,
    altitud: float | None = None,
) -> dict:
    """Estima la serie climatológica NDVI (MODIS/Landsat/Sentinel-2) calibrada para la parcela."""
    base = _cargar_curva_respaldo()
    # Ajuste espacial leve por gradiente latitudinal/longitudinal y lluvia local en Chimborazo
    ajuste_geo = 0.02 * math.sin((lat - LAT_CHIMBORAZO) * 4.0) - 0.015 * (lon - LON_CHIMBORAZO)
    ajuste_alt = -0.02 * clamp(((altitud - 2850) / 800) if altitud is not None else 0.0, -0.5, 1.0)

    curva = []
    for i, val in enumerate(base):
        mod_lluvia = 0.0
        if lluvia_mensual and len(lluvia_mensual) == 12:
            # Meses más lluviosos elevan ligeramente el vigor; verano seco (Jul-Sep) mantiene estrés
            mod_lluvia = clamp((lluvia_mensual[i] - 90.0) / 1800.0, -0.04, 0.04)
        # En verano andino (jul-sep) mantenemos la señal de suelo descubierto cuando hay baja cobertura
        es_verano = i in (6, 7, 8)
        techo = 0.28 if es_verano and val <= UMBRAL_SUELO_DESNUDO else MAX_NDVI
        v = clamp(val + ajuste_geo + ajuste_alt + mod_lluvia, MIN_NDVI, techo)
        curva.append(round(v, 3))

    return reconstruir_desde_curva(
        curva,
        fuente="NASA MODIS / Landsat / Sentinel-2 (climatología Chimborazo)",
        mes_actual=mes_actual,
    )
