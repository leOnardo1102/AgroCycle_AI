"""Guía rápida de AgroCycle AI: ventana emergente disponible desde la barra lateral y la página de inicio.

Se abre sola la primera vez que alguien entra en la sesión (útil para jurados y usuarios nuevos)
y después solo cuando se pulsa «Guía rápida».
"""
import streamlit as st


@st.dialog("Guía rápida — AgroCycle AI", width="large")
def mostrar():
    st.markdown(
        "**AgroCycle AI** ayuda a planificar la rotación de cultivos en Chimborazo combinando datos satelitales "
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


def boton(clave: str, ancho: str = "stretch"):
    """Botón «Guía rápida» que abre la ventana."""
    if st.button("Guía rápida", icon=":material/help:", width=ancho, key=clave):
        st.session_state.guia_vista = True
        mostrar()


def abrir_la_primera_vez():
    """Muestra la guía automáticamente una sola vez por sesión."""
    if not st.session_state.get("guia_vista"):
        st.session_state.guia_vista = True
        mostrar()
