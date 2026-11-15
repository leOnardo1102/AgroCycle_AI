"""AgroCycle AI - apoyo a la decisión de rotación de cultivos con datos de la NASA (Chimborazo, Ecuador).

Ejecutar:  streamlit run app.py
"""
import os
import sys

import streamlit as st

st.set_page_config(page_title="AgroCycle AI", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

_RELOAD_TAG = "agrocycle_v4_satelite_2026"
if os.environ.get("_AGROCYCLE_RELOAD_TAG") != _RELOAD_TAG:
    _PREFIJOS_RECARGA = ("config", "utils", "services", "modules", "ui", "vistas")
    for _mod in [k for k in sys.modules if k == "config" or k.startswith(tuple(p + "." for p in _PREFIJOS_RECARGA))]:
        sys.modules.pop(_mod, None)
    os.environ["_AGROCYCLE_RELOAD_TAG"] = _RELOAD_TAG

from database.conexion import inicializar  # noqa: E402
from modules import parcelas, tecnicos  # noqa: E402
from ui import theme  # noqa: E402
from vistas import guia  # noqa: E402
from vistas import acerca, cartera, catalogo, comun, inicio, parcela, perfil, registro  # noqa: E402


@st.cache_resource
def _bd():
    inicializar()
    return True


_bd()
comun.estilos()
ss = st.session_state
if ss.get("_reload_tag") != _RELOAD_TAG:
    for _k in [k for k in ss if k.startswith(("prep_", "res_", "sim_"))]:
        del ss[_k]
    ss["_reload_tag"] = _RELOAD_TAG
ss.setdefault("modo", "agricultor")
ss.setdefault("pagina", "inicio")

# ------------------------------------------------------------------ barra lateral
ICONOS_MENU = {
    "perfil": ":material/badge:",
    "cartera": ":material/groups:",
    "inicio": ":material/dashboard:",
    "registro": ":material/add_location_alt:",
    "parcela": ":material/agriculture:",
    "catalogo": ":material/menu_book:",
    "acerca": ":material/info:",
}

with st.sidebar:
    theme.marca()
    guia.boton("guia_lateral")
    theme.seccion("Vista")
    vista = st.segmented_control(
        "Vista",
        ["Agricultor", "Técnica"],
        default="Agricultor" if ss.modo == "agricultor" else "Técnica",
        label_visibility="collapsed",
        key="vista_ctrl",
        width="stretch",
        help="La vista técnica muestra los datos satelitales, puntajes y reglas usadas.",
    )
    if vista:  # el control segmentado devuelve None si se vuelve a tocar la opción activa
        ss.modo = "agricultor" if vista == "Agricultor" else "tecnica"

    tecs = tecnicos.listar()
    if tecs:
        tids = [t.id_tecnico for t in tecs]
        if ss.get("tecnico_id") not in tids:
            ss.tecnico_id = tids[0]
        theme.seccion("Técnico responsable")
        ss.tecnico_id = st.selectbox(
            "Técnico responsable",
            tids,
            index=tids.index(ss.tecnico_id),
            label_visibility="collapsed",
            format_func=lambda i: next(t.nombre for t in tecs if t.id_tecnico == i),
            help="Sus datos salen en el encabezado y la firma de la hoja, el PDF y los mensajes.",
        )
        t = next(t for t in tecs if t.id_tecnico == ss.tecnico_id)
        detalle_tec = " · ".join(x for x in [t.cargo, t.institucion] if x)
        theme.persona(t.nombre, detalle_tec or (t.canton_parroquia or ""))

    agricultores = parcelas.listar_agricultores()
    if agricultores:
        ids = [a.id_agricultor for a in agricultores]
        if ss.get("agricultor_id") not in ids:
            ss.agricultor_id = ids[0]
        theme.seccion("Agricultor en atención")
        aid = st.selectbox(
            "Agricultor en atención",
            ids,
            index=ids.index(ss.agricultor_id),
            label_visibility="collapsed",
            format_func=lambda i: next(a.nombre for a in agricultores if a.id_agricultor == i),
        )
        if aid != ss.agricultor_id:
            ss.agricultor_id, ss.parcela_id, ss.pagina = aid, None, "inicio"
            st.rerun()
        a = next(a for a in agricultores if a.id_agricultor == ss.agricultor_id)
        theme.persona(a.nombre, " · ".join(x for x in [a.comunidad, a.telefono] if x))

    st.divider()
    theme.seccion("Menú")
    paginas = {"perfil": "Mi perfil de técnico", "cartera": "Cartera de agricultores"}
    if ss.get("agricultor_id"):
        paginas |= {"inicio": "Parcelas del agricultor", "registro": "Registrar parcela"}
        if ss.get("parcela_id"):
            p = parcelas.obtener(ss.parcela_id)
            if p and p.id_agricultor == ss.agricultor_id:
                paginas["parcela"] = p.nombre
    if ss.modo == "tecnica":
        paginas["catalogo"] = "Catálogo y reglas"
    paginas["acerca"] = "Acerca y limitaciones"
    if ss.pagina not in paginas:
        ss.pagina = "inicio" if ss.get("agricultor_id") else "cartera"
    with st.container(key="menu"):
        for k, v in paginas.items():
            if st.button(
                v,
                icon=ICONOS_MENU[k],
                width="stretch",
                type="primary" if ss.pagina == k else "secondary",
                key=f"nav_{k}",
            ):
                ss.pagina = k
                if k == "registro":
                    ss.editar_id = None
                st.rerun()
    st.divider()
    st.caption("Datos: NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat y SoilGrids. Orientativo; no reemplaza al técnico agrícola.")

# ------------------------------------------------------------------ contenido
guia.abrir_la_primera_vez()  # la guía se abre sola en la primera visita de cada sesión
if ss.pagina == "perfil":
    perfil.mostrar()
elif ss.pagina == "cartera" or not ss.get("agricultor_id"):
    cartera.mostrar()
elif ss.pagina == "registro":
    registro.mostrar()
elif ss.pagina == "parcela" and ss.get("parcela_id"):
    parcela.mostrar(ss.parcela_id)
elif ss.pagina == "catalogo":
    catalogo.mostrar()
elif ss.pagina == "acerca":
    acerca.mostrar()
else:
    inicio.mostrar()

ss.pagina_anterior = ss.pagina  # para saber cuándo se entra de nuevo a una página
