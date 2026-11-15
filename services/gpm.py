"""NASA GPM / IMERG (~10 km) - frecuencia de lluvias intensas y riesgo de lavado de suelo.

Usa la climatología de eventos convectivos calibrada para Chimborazo (respaldo offline en
data/nasa_respaldo_chimborazo.json) y estima el riesgo de erosividad y lavado superficial
combinado con la pendiente del terreno.
"""
import json

from config import LAT_CHIMBORAZO, LON_CHIMBORAZO, RESPALDO_NASA
from utils.calculos import MESES_L, clamp

_GPM_BASE = {
    "dias_lluvia_intensa_anual": 14,
    "intensidad_max_mm_dia": 29.5,
    "frecuencia_mensual_intensa": [1.2, 1.8, 2.4, 2.5, 1.4, 0.6, 0.2, 0.1, 0.3, 1.5, 1.8, 1.2],
}


def _cargar_base() -> dict:
    if RESPALDO_NASA.exists():
        try:
            data = json.loads(RESPALDO_NASA.read_text(encoding="utf-8")).get("gpm")
            if isinstance(data, dict) and len(data.get("frecuencia_mensual_intensa", [])) == 12:
                return data
        except (ValueError, OSError):
            pass
    return dict(_GPM_BASE)


def evaluar_lavado(
    frecuencia_mensual: list[float],
    intensidad_max_mm_dia: float,
    pendiente: float = 8.0,
    fuente: str = "NASA GPM IMERG (climatología Chimborazo)",
) -> dict:
    """Calcula riesgo de lavado de suelo e índice de erosividad a partir de eventos intensos."""
    freq = [round(max(0.0, float(x)), 2) for x in frecuencia_mensual[:12]]
    if len(freq) < 12:
        freq = (freq + list(_GPM_BASE["frecuencia_mensual_intensa"]))[:12]

    dias_anuales = round(sum(freq), 1)
    umbral_pico = max(1.6, max(freq) * 0.72)
    meses_pico = [i for i, v in enumerate(freq) if v >= umbral_pico]
    nombres_pico = [MESES_L[i] for i in meses_pico]

    # Índice de erosividad combinando días intensos, intensidad máxima y pendiente de ladera
    pend = max(0.0, float(pendiente))
    factor_pend = 1.0 + pend / 15.0
    erosividad = round((dias_anuales * intensidad_max_mm_dia * 0.65) * (0.7 + pend / 30.0), 1)
    puntaje_lavado = dias_anuales * factor_pend + intensidad_max_mm_dia * 0.35

    if puntaje_lavado >= 38 or (pend >= 12 and dias_anuales >= 12):
        riesgo = "alto"
        recomendacion = (
            "Riesgo alto de lavado de suelo y nutrientes: evitar suelo descubierto entre "
            f"{', '.join(nombres_pico[:3]) or 'época de lluvias'}, sembrar en curvas de nivel y fraccionar la fertilización."
        )
    elif puntaje_lavado >= 22:
        riesgo = "moderado"
        recomendacion = (
            "Lluvias intensas moderadas: mantener rastrojo picado o cobertura viva y evitar labores profundas en meses pico."
        )
    else:
        riesgo = "bajo"
        recomendacion = "Frecuencia baja de aguaceros erosivos; mantener manejo conservacionista habitual."

    return {
        "fuente": fuente,
        "resolucion": "~10 km",
        "frecuencia_mensual_intensa": freq,
        "dias_lluvia_intensa_anual": dias_anuales,
        "intensidad_max_mm_dia": round(float(intensidad_max_mm_dia), 1),
        "meses_pico_intensidad": meses_pico,
        "meses_pico_nombres": nombres_pico,
        "riesgo_lavado": riesgo,
        "indice_erosividad_r": erosividad,
        "recomendacion_manejo": recomendacion,
    }


def consultar(
    lat: float,
    lon: float,
    lluvia_mensual: list[float] | None = None,
    pendiente: float = 8.0,
) -> dict:
    """Estima la frecuencia mensual de lluvias intensas (NASA GPM IMERG) y el riesgo de lavado."""
    base = _cargar_base()
    freq_base = base["frecuencia_mensual_intensa"]
    intensidad_base = float(base.get("intensidad_max_mm_dia", 29.5))

    # Ajuste ligero hacia estribaciones occidentales/orientales y modulación por lluvia mensual observada
    factor_geo = clamp(1.0 + 0.08 * (LAT_CHIMBORAZO - lat) - 0.12 * (lon - LON_CHIMBORAZO), 0.75, 1.35)
    freq = []
    for i, f in enumerate(freq_base):
        if lluvia_mensual and len(lluvia_mensual) == 12:
            escala_m = clamp(lluvia_mensual[i] / 110.0, 0.5, 1.5)
            val = f * (0.65 + 0.35 * escala_m) * factor_geo
        else:
            val = f * factor_geo
        freq.append(round(val, 2))

    intensidad = round(intensidad_base * (0.85 + 0.15 * factor_geo), 1)
    return evaluar_lavado(freq, intensidad, pendiente=pendiente)
