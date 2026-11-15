"""Constantes generales de AgroCycle AI."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Centro de referencia: Riobamba, Chimborazo
LAT_CHIMBORAZO, LON_CHIMBORAZO = -1.6635, -78.6546

# Tiempo máximo de espera de cada fuente externa (segundos).
# NASA POWER suele tardar 3-10 s; con menos de 8 s caería al respaldo con demasiada frecuencia.
TIMEOUT_NASA_S = 8
TIMEOUT_SRTM_S = 8
TIMEOUT_SOILGRIDS_S = 10

# Respuesta real de NASA POWER para Riobamba: se usa si NASA no responde y la parcela no tiene datos guardados
RESPALDO_NASA = RAIZ / "data" / "nasa_respaldo_chimborazo.json"
FUENTE_RESPALDO = "NASA POWER (respaldo Chimborazo)"

# Días que se reutilizan los datos guardados antes de volver a consultar
VIGENCIA_DATOS_DIAS = 30
