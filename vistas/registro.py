"""Registro y edición de parcelas (CU-01, RF-01, RF-02, RF-04 a RF-06)."""
import json

import streamlit as st

from modules import parcelas
from modules.datos_ambientales import CANTONES
from ui import theme
from utils.validaciones import AGUA, DRENAJE, PROBLEMAS, TEXTURAS, TIERRA_SENCILLA
from vistas import mapa_parcela
from vistas.comun import encabezado, es_tecnica, ir

PENDIENTES = {"No sé": None, "Plano": 2.0, "Un poco inclinado": 8.0, "Inclinado": 18.0, "Muy inclinado": 35.0}


def mostrar():
    ss = st.session_state
    editando = parcelas.obtener(ss.editar_id) if ss.get("editar_id") else None
    encabezado(
        "Editar parcela" if editando else "Registrar parcela",
        "Marca el terreno en el mapa satelital y completa sus datos",
        miga="Parcelas",
        icono_miga="pin",
    )
    if "reg_punto" not in ss or ss.get("reg_de") != (editando.id_parcela if editando else None):
        ss.reg_de = editando.id_parcela if editando else None
        ss.reg_punto = (editando.latitud, editando.longitud) if editando else (CANTONES[0]["lat"], CANTONES[0]["lon"])
        ss.reg_poligono = json.loads(editando.poligono) if editando and editando.poligono else None
        ss.reg_zoom = 18 if editando else 16
        ss.mp_modo = "esquinas"
        ss.mp_cerrado = bool(ss.reg_poligono)

    listo_mapa = bool(ss.reg_poligono) or ss.get("mp_modo") == "punto" or bool(editando)
    theme.pasos(2 if listo_mapa else 1)
    area_dib = mapa_parcela.selector(editando, ndvi=es_tecnica())

    with st.form("form_parcela"):
        theme.subtitulo_icono("capas", "2. Datos de suelo y agua")
        nombre = st.text_input("Nombre de la parcela", value=editando.nombre if editando else "", placeholder="Ej. Terreno de abajo", key="nombre_parcela")
        sup_def = area_dib or (editando.superficie if editando else 1.0)
        superficie = st.number_input("Tamaño aproximado (hectáreas)", min_value=0.01, max_value=500.0, value=max(0.01, float(round(sup_def, 2))), step=0.25,
                                     help="1 cuadra ≈ 0,7 ha. Si dibujaste el contorno, se calcula solo.")
        agua_keys = list(AGUA)
        agua = st.radio("¿Tienes agua de riego?", agua_keys, format_func=AGUA.get, horizontal=True,
                        index=agua_keys.index(editando.disponibilidad_agua) if editando else 1)
        if es_tecnica():
            pend = st.number_input("Pendiente (%) · vacío = usar NASA SRTM", min_value=0.0, max_value=150.0,
                                   value=editando.pendiente if editando and editando.pendiente is not None else None, step=1.0)
        else:
            inv = {v: k for k, v in PENDIENTES.items() if v is not None}
            actual = inv.get(editando.pendiente, "No sé") if editando else "No sé"
            pend = PENDIENTES[st.radio("¿Cómo es tu terreno?", list(PENDIENTES), horizontal=True, index=list(PENDIENTES).index(actual),
                                       help="Si no sabes, la calculamos con el relieve de la NASA.")]
        problemas = st.multiselect("¿Qué problemas has visto en tu terreno? (opcional)", list(PROBLEMAS), format_func=PROBLEMAS.get,
                                   placeholder="Elige uno o varios (opcional)", default=editando.lista_problemas if editando else [])
        ph = mo = textura = None
        if es_tecnica():
            st.markdown("**Suelo (opcional).** Deja vacío lo que no conozcas: se estimará con SoilGrids.")
            t1, t2, t3 = st.columns(3)
            ph = t1.number_input("pH", min_value=3.5, max_value=9.5, value=editando.ph if editando else None, step=0.1)
            mo = t2.number_input("Materia orgánica (%)", min_value=0.0, max_value=30.0, value=editando.materia_organica if editando else None, step=0.1)
            tex_ops = [None] + list(TEXTURAS)
            textura = t3.selectbox("Textura", tex_ops, format_func=lambda k: "No sé" if k is None else TEXTURAS[k],
                                   index=tex_ops.index(editando.textura) if editando and editando.textura in tex_ops else 0)
            drenaje = st.selectbox("Drenaje", list(DRENAJE), format_func=DRENAJE.get,
                                   index=list(DRENAJE).index(editando.drenaje) if editando and editando.drenaje in DRENAJE else 1)
        else:
            if editando:
                ph, mo = editando.ph, editando.materia_organica
            ops = [None] + list(TIERRA_SENCILLA)
            actual_t = editando.textura if editando and editando.textura in TIERRA_SENCILLA else None
            textura = st.radio("¿Cómo es tu tierra?", ops, horizontal=True, index=ops.index(actual_t),
                               format_func=lambda k: "No sé" if k is None else TIERRA_SENCILLA[k])
            if textura is None and editando and editando.textura not in TIERRA_SENCILLA:
                textura = editando.textura  # conservar lo que registró el técnico
            drenaje = st.radio("¿Qué pasa cuando llueve fuerte?", list(DRENAJE), horizontal=True, format_func=DRENAJE.get,
                               index=list(DRENAJE).index(editando.drenaje) if editando and editando.drenaje in DRENAJE else 1)
        obs = st.text_area("Observaciones (opcional)", value=(editando.observaciones or "") if editando else "")
        enviado = st.form_submit_button("Guardar y continuar al plan anual", icon=":material/arrow_forward:", type="primary", width="stretch")
    if enviado:
        if mapa_parcela.contorno_pendiente(ss):
            if not mapa_parcela.contorno_cruzado(ss.get("mp_vertices") or []):
                mapa_parcela.confirmar_contorno(ss)
            else:
                st.error("Algunas líneas se cruzan en el terreno marcado. Corrige los puntos tocándolos en orden antes de guardar.", icon=":material/polyline:")
                return
        if ss.get("reg_poligono") and (not superficie or superficie == 1.0):
            area_pol = mapa_parcela.area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
            if area_pol:
                superficie = max(0.01, float(round(area_pol, 2)))
        datos = {"nombre": nombre, "latitud": ss.reg_punto[0], "longitud": ss.reg_punto[1], "superficie": superficie,
                 "disponibilidad_agua": agua, "pendiente": pend, "observaciones": obs or None, "problemas": problemas,
                 "ph": ph, "materia_organica": mo, "textura": textura, "drenaje": drenaje,
                 "poligono": json.dumps(ss.reg_poligono) if ss.reg_poligono else None}
        try:
            p = parcelas.editar(editando.id_parcela, datos) if editando else parcelas.registrar(ss.agricultor_id, datos)
        except parcelas.DatosInvalidos as e:
            for err in e.errores:
                st.error(err)
            return
        for k in ("reg_punto", "reg_poligono", "reg_de", "mp_centro", "mp_vertices", "mp_ultimo_dibujo", "mp_cerrado"):
            ss.pop(k, None)
        ss.pop(f"res_{p.id_parcela}", None)
        st.success("Parcela guardada", icon=":material/check_circle:")
        ir("parcela", parcela_id=p.id_parcela, editar_id=None)
