"""Guía rápida de AgroCycle: ventana emergente disponible desde la barra lateral y la página de inicio.

Se abre sola la primera vez que alguien entra en la sesión (útil para jurados y usuarios nuevos)
y después siempre que se pulse «Guía rápida» en la barra lateral o en el panel de inicio.
"""
import streamlit as st
from ui.i18n import en_ingles


def _contenido():
    if en_ingles():
        st.markdown(
            "**AgroCycle** helps plan crop rotations in Chimborazo by combining satellite and agroclimatic data "
            "(**NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat**, and **SoilGrids**) with each field's history."
        )
        st.markdown("#### Try it in 3 steps")
        c1, c2, c3 = st.columns(3)
        c1.markdown("**1. Choose your view**  \nIn the left panel: **Farmer** (plain field language) or **Technical** "
                    "(agronomic indicators and satellite metrics).")
        c2.markdown("**2. Open a field**  \nUnder **Farmer's fields**, tap **Open field** on a field "
                    "*Ready for planning*, or register a new one on the map with **New field**.")
        c3.markdown("**3. Generate rotation plan**  \nIn the **Crop plan** tab, tap **Generate my crop plan**. "
                    "Then check **Compare** and **What if…?**")
        st.markdown("#### What you will find in each field")
        st.markdown(
            "- **Diagnosis:** rainfall, frost risk, water availability, terrain, and soil cover.\n"
            "- **Crop plan:** three 12-month rotation alternatives compared to current practices.\n"
            "- **Compare:** soil, water, climate, and plant health scores versus status quo.\n"
            "- **What if…?:** see how the plan adapts to dry, wet, warmer, or frost-prone years.\n"
            "- **Handover:** send the plan via WhatsApp or download as a PDF report."
        )
        st.info("Recommendations are indicative and complement the field agricultural technician's criteria.",
                icon=":material/info:")
        if st.button("Got it, let's start", type="primary", width="stretch", key="guia_cerrar"):
            st.rerun()
    else:
        st.markdown(
            "**AgroCycle** ayuda a planificar la rotación de cultivos en Chimborazo combinando datos satelitales "
            "y agroclimáticos (**NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat** y **SoilGrids**) con el historial "
            "de cada parcela."
        )
        st.markdown("#### Pruébala en 3 pasos")
        c1, c2, c3 = st.columns(3)
        c1.markdown("**1. Elige la vista**  \nEn el panel izquierdo: **Agricultor** (lenguaje sencillo) o **Técnica** "
                    "(indicadores agronómicos y datos satelitales).")
        c2.markdown("**2. Abre una parcela**  \nEn **Parcelas del agricultor** pulsa **Abrir parcela** en un terreno "
                    "*Lista para planificar*, o registra uno nuevo en el mapa con **Nueva parcela**.")
        c3.markdown("**3. Genera el plan**  \nEn la pestaña **Plan de cultivo** pulsa **Generar mi plan de cultivo**. "
                    "Luego mira **Comparar** y **¿Qué pasa si…?**")
        st.markdown("#### Qué encontrarás en cada parcela")
        st.markdown(
            "- **Diagnóstico:** lluvia, heladas, agua, terreno y cobertura del suelo.\n"
            "- **Plan de cultivo:** tres rotaciones para 12 meses comparadas con lo que se siembra hoy.\n"
            "- **Comparar:** puntajes de suelo, agua, clima y sanidad frente al manejo actual.\n"
            "- **¿Qué pasa si…?:** cómo cambia el plan con un año seco, lluvioso, más calor o heladas.\n"
            "- **Entrega:** envía el plan por WhatsApp o descárgalo en PDF."
        )
        st.info("Las recomendaciones son orientativas y complementan el criterio del técnico agrícola en campo.",
                icon=":material/info:")
        if st.button("Entendido, empezar", type="primary", width="stretch", key="guia_cerrar"):
            st.rerun()


@st.dialog("Guía rápida — AgroCycle", width="large")
def _dialogo_es():
    _contenido()


@st.dialog("Quick guide — AgroCycle", width="large")
def _dialogo_en():
    _contenido()


def mostrar():
    """Abre la guía en el idioma activo (el título de una ventana de Streamlit es fijo, por eso hay dos)."""
    (_dialogo_en if en_ingles() else _dialogo_es)()


def boton(clave: str, ancho: str = "stretch"):
    """Botón «Guía rápida» que abre la ventana modal de forma segura y consistente."""
    if st.button("Guía rápida", icon=":material/help:", width=ancho, key=clave):
        st.session_state["guia_vista"] = True
        st.session_state["abrir_guia"] = True
        st.rerun()


def revisar_apertura():
    """Muestra la guía automáticamente la primera vez por sesión o al pulsar cualquier botón de guía."""
    ss = st.session_state
    if not ss.get("guia_vista"):
        ss["guia_vista"] = True
        mostrar()
    elif ss.pop("abrir_guia", False):
        mostrar()


abrir_la_primera_vez = revisar_apertura
