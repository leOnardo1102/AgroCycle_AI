"""Perfil del técnico agropecuario: sus datos salen en la hoja impresa, el PDF y los mensajes al agricultor."""
from html import escape

import pandas as pd
import streamlit as st

from modules import tecnicos
from modules.parcelas import DatosInvalidos
from ui import theme
from vistas.comun import encabezado


def mostrar():
    ss = st.session_state
    encabezado(
        "Perfil del técnico",
        "Tus datos aparecen en el encabezado y la firma de los planes, PDF y mensajes",
        miga="Técnico",
        icono_miga="usuarios",
    )
    lista = tecnicos.listar()
    actual = tecnicos.obtener(ss.get("tecnico_id"))

    theme.kpis([
        ("Técnicos registrados", len(lista), "en el equipo", "usuarios", theme.VERDE),
        ("Técnico activo", actual.nombre if actual else "Sin definir", (actual.institucion or "Sin institución") if actual else "Registra tus datos", "escudo", "#0E7490"),
        ("Cantón / parroquia", (actual.canton_parroquia or "No definido") if actual else "—", "zona de atención", "pin", "#7C3AED"),
    ])

    if lista:
        theme.subtitulo_icono("usuarios", "Equipo técnico registrado")
        st.dataframe(
            pd.DataFrame([
                {
                    "Nombre": t.nombre,
                    "Cargo": t.cargo or "",
                    "Institución": t.institucion or "",
                    "Cantón / parroquia": t.canton_parroquia or "",
                    "Celular": t.telefono or "",
                    "Correo": t.correo or "",
                }
                for t in lista
            ]),
            hide_index=True,
            width="stretch",
        )

    modo = st.radio(
        "Acción",
        ["editar", "nuevo"],
        horizontal=True,
        format_func={"editar": f"Editar mis datos ({actual.nombre})" if actual else "Editar", "nuevo": "Registrar otro técnico"}.get,
        index=0 if actual else 1,
        disabled=not actual,
    )
    t = actual if modo == "editar" and actual else None
    with st.form("form_tecnico", clear_on_submit=t is None):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre completo *", value=t.nombre if t else "", placeholder="Ej. Ing. Ana Pérez")
        cargo = c2.text_input("Cargo", value=(t.cargo or "") if t else "", placeholder="Ej. Técnica de extensión agrícola")
        c1, c2 = st.columns(2)
        inst = c1.text_input("Institución", value=(t.institucion or "") if t else "", placeholder="Ej. MAG Chimborazo / GAD Provincial / Cooperativa")
        lugar = c2.text_input("Cantón / parroquia", value=(t.canton_parroquia or "") if t else "", placeholder="Ej. Riobamba, Licto")
        c1, c2 = st.columns(2)
        tel = c1.text_input("Celular", value=(t.telefono or "") if t else "", placeholder="09XXXXXXXX")
        cor = c2.text_input("Correo", value=(t.correo or "") if t else "")
        ok = st.form_submit_button("Guardar", icon=":material/save:", type="primary", width="stretch")
    if ok:
        datos = {"nombre": nombre, "cargo": cargo, "institucion": inst, "canton_parroquia": lugar, "telefono": tel, "correo": cor}
        try:
            r = tecnicos.editar(t.id_tecnico, datos) if t else tecnicos.registrar(datos)
        except DatosInvalidos as e:
            for err in e.errores:
                st.error(err)
            return
        ss.tecnico_id = r.id_tecnico
        st.success(f"Datos de {r.nombre} guardados. Ahora es el técnico responsable activo.", icon=":material/check_circle:")
        st.rerun()

    if actual:
        theme.subtitulo_icono("lapiz", "Vista previa de tu firma en la hoja impresa y PDF")
        st.markdown(
            f"<div class='tarjeta' style='text-align:center'>______________________________<br><b>{escape(actual.nombre)}</b><br>"
            f"<small>{escape(', '.join(x for x in (actual.cargo, actual.institucion) if x))}</small><br>"
            f"<small>{escape(actual.contacto)}</small></div>",
            unsafe_allow_html=True,
        )
