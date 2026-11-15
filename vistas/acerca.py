"""Información del proyecto, fuentes satelitales, fusión multiescala y limitaciones."""
import pandas as pd
import streamlit as st

from modules import datos_ambientales as amb
from ui import theme
from vistas.comun import encabezado


def mostrar():
    encabezado(
        "Acerca de AgroCycle",
        "Cómo funciona, fusión multiescala de observación de la Tierra y limitaciones",
        miga="Información",
        icono_miga="satelite",
    )
    st.write(
        "Herramienta de apoyo a la toma de decisiones para la rotación de cultivos de pequeños productores de Chimborazo, "
        "desarrollada para el NASA Space Apps Challenge."
    )

    theme.subtitulo_icono("brote", "¿Cómo decide el motor agronómico?")
    st.markdown("""
1. Reúne el **historial** de la parcela, lo que indicó el agricultor y las **capas ambientales NASA + SoilGrids**.
2. Descarta los cultivos que no se dan a la altura SRTM de la parcela (regla R05).
3. Evalúa todas las secuencias posibles de 3 etapas anuales o 3–4 ciclos multianuales y filtra las que incumplen **restricciones esenciales** (como repetir papa antes de 2 ciclos).
4. Simula mes a mes el **agua** (lluvia, evapotranspiración, riego y humedad superficial SMAP), el **nitrógeno**, las **heladas**, la **erosión en ladera/lavado** y el **pH**.
5. Compara cada plan recomendado contra el **escenario testigo sin rotación** (repetir el mismo cultivo todo el año) y presenta hasta 3 opciones diferenciadas.
""")

    theme.subtitulo_icono("satelite", "Fuentes de observación de la Tierra integradas")
    fuentes_df = pd.DataFrame([
        {"Fuente": "NASA POWER (MERRA-2)", "Estado": "Integrado (API + respaldo Chimborazo)", "Uso en AgroCycle": "Lluvia, temperatura media/mín./máx., radiación solar y humedad radicular, corregidas por altitud."},
        {"Fuente": "NASA SRTM (30 m)", "Estado": "Integrado (OpenTopoData)", "Uso en AgroCycle": "Altitud, pendiente (%) y nivel de riesgo de erosión en ladera (factor LS)."},
        {"Fuente": "MODIS / Landsat / Sentinel-2 NDVI", "Estado": "Integrado (climatología + capa GIBS)", "Uso en AgroCycle": "Curva estacional NDVI (0,15–0,85), detección de meses críticos de suelo desnudo y alerta de erosión."},
        {"Fuente": "NASA GPM IMERG (~10 km)", "Estado": "Integrado (climatología calibrada)", "Uso en AgroCycle": "Frecuencia de lluvias intensas e intensidad máxima para estimar riesgo de lavado de suelo."},
        {"Fuente": "NASA SMAP L3/L4 (9–36 km)", "Estado": "Integrado (climatología + simulador)", "Uso en AgroCycle": "Humedad superficial del suelo y anomalía hídrica conectadas al simulador de escenarios."},
        {"Fuente": "SoilGrids (ISRIC, 250 m)", "Estado": "Integrado (API complementaria)", "Uso en AgroCycle": "Estimación de pH, materia orgánica y textura USDA cuando no hay análisis de laboratorio."},
    ])
    st.dataframe(fuentes_df, hide_index=True, width="stretch")

    theme.subtitulo_icono("capas", "Fusión de Datos Satelitales y Escalas")
    st.markdown(
        "<div class='tarjeta'>Cada sensor observa la Tierra a una escala espacial distinta. AgroCycle armoniza estas resoluciones "
        "al polígono de la parcela combinando muestreo topográfico fino (30 m), corrección térmica por gradiente andino "
        "(-0,58 °C/100 m), calibración cantonal de lluvia y validación obligatoria en campo.</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(amb.TABLA_FUSION_ESCALAS), hide_index=True, width="stretch")

    theme.subtitulo_icono("alerta", "Limitaciones y rol irremplazable del técnico")
    st.warning(
        "- Es una herramienta **de apoyo**: no reemplaza a un técnico agrícola ni un análisis de suelo de laboratorio.\n"
        "- Los datos satelitales tienen incertidumbre espacial según su resolución (30 m en SRTM hasta ~50 km en NASA POWER) "
        "y no detectan plagas subterráneas (gusano blanco, nematodos), compactación puntual ni turnos reales de agua.\n"
        "- Los parámetros de cultivos, precios y costos son **referenciales** y están pendientes de validación local (RN-10).\n"
        "- Los escenarios del simulador son **hipotéticos**, no pronósticos meteorológicos ni de mercado."
    )

    theme.subtitulo_icono("escudo", "Privacidad")
    st.write(
        "Los datos de las parcelas se guardan en la base de datos local SQLite de la aplicación y solo se usan para generar recomendaciones. "
        "Las coordenadas se envían únicamente a NASA POWER, OpenTopoData (SRTM) y SoilGrids para obtener las capas ambientales."
    )
