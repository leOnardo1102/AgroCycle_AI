"""Cartera del técnico agropecuario: agricultores con sus datos de contacto (para entregarles el plan)."""
from html import escape

import streamlit as st

from modules import parcelas, recomendaciones
from ui import theme
from vistas.comun import encabezado, fmt, ir


def mostrar():
    ss = st.session_state
    encabezado(
        "Cartera de agricultores",
        "Agricultores que acompañas. Sus datos de contacto se usan para enviarles el plan por WhatsApp o correo.",
        miga="Técnico",
        icono_miga="usuarios",
    )
    lista = parcelas.listar_agricultores()
    if lista:
        filas = []
        for a in lista:
            ps = parcelas.listar(a.id_agricultor)
            planes = [pl for p in ps for pl in recomendaciones.listar_planes(p.id_parcela)]
            filas.append({
                "a": a,
                "parcelas": len(ps),
                "ha": round(sum(p.superficie for p in ps), 2),
                "plan": max(pl["fecha"] for pl in planes) if planes else None,
            })
        theme.kpis([
            ("Agricultores", len(filas), "en tu cartera", "usuarios", theme.VERDE),
            ("Parcelas", sum(x["parcelas"] for x in filas), "registradas", "mapa", "#0E7490"),
            ("Superficie", f"{fmt(sum(x['ha'] for x in filas), 2)} ha", "acompañada", "capas", "#7C3AED"),
            ("Con plan entregado", f"{sum(1 for x in filas if x['plan'])} / {len(filas)}", "agricultores", "calendario", "#0284C7"),
        ])
        anchos = [3.3, 1.5, 1.4, 1.3, 1.7, 0.55, 0.55]
        with st.container(key="cartera_cab"):
            for col, c in zip(st.columns(anchos), ["Agricultor", "Comunidad", "Celular", "Parcelas", "Último plan", "", ""]):
                col.markdown(f"<div class='tabla-cab'>{c}</div>", unsafe_allow_html=True)
        with st.container(key="cartera"):
            for x in filas:
                a = x["a"]
                c = st.columns(anchos, vertical_alignment="center")
                detalle = "<br>".join(escape(v) for v in [f"C.I. {a.documento}" if a.documento else "", a.correo or ""] if v) or "Sin datos de contacto"
                c[0].markdown(
                    f"<div class='fila-nombre'>{theme.avatar(a.nombre)}<div><b>{escape(a.nombre)}</b>"
                    f"<small>{detalle}</small></div></div>",
                    unsafe_allow_html=True,
                )
                c[1].markdown(f"<div class='celda'>{escape(a.comunidad or '—')}</div>", unsafe_allow_html=True)
                c[2].markdown(f"<div class='celda'>{escape(a.telefono or '—')}</div>", unsafe_allow_html=True)
                c[3].markdown(f"<div class='celda'><b>{x['parcelas']}</b> · {fmt(x['ha'], 2)} ha</div>", unsafe_allow_html=True)
                c[4].markdown(
                    theme.insignia(f"Entregado {x['plan']:%d/%m/%Y}", "ok") if x["plan"] else theme.insignia("Sin plan", "falta"),
                    unsafe_allow_html=True,
                )
                if c[5].button(
                    "",
                    key=f"ver_{a.id_agricultor}",
                    icon=":material/agriculture:",
                    width="stretch",
                    help="Ver sus parcelas",
                    type="primary" if a.id_agricultor == ss.get("agricultor_id") else "secondary",
                ):
                    ir("inicio", agricultor_id=a.id_agricultor, parcela_id=None)
                if c[6].button("", key=f"edit_{a.id_agricultor}", icon=":material/edit:", width="stretch", help="Editar sus datos"):
                    ss.editar_agricultor = a.id_agricultor
                    st.rerun()
        st.write("")

    editando = parcelas.obtener_agricultor(ss.get("editar_agricultor")) if ss.get("editar_agricultor") else None
    theme.subtitulo_icono("lapiz" if editando else "usuarios", "Editar agricultor" if editando else "Registrar agricultor")
    with st.form("form_agricultor", clear_on_submit=not editando):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombres y apellidos *", value=editando.nombre if editando else "")
        documento = c2.text_input("Cédula", value=(editando.documento or "") if editando else "", max_chars=10)
        c1, c2, c3 = st.columns(3)
        comunidad = c1.text_input("Comunidad / parroquia", value=(editando.comunidad or "") if editando else "", placeholder="Ej. Licto, Quimiag, Guamote")
        telefono = c2.text_input("Celular (WhatsApp)", value=(editando.telefono or "") if editando else "", placeholder="09XXXXXXXX")
        correo = c3.text_input("Correo electrónico", value=(editando.correo or "") if editando else "")
        b1, b2 = st.columns([1, 1])
        guardar = b1.form_submit_button("Guardar", icon=":material/save:", type="primary", width="stretch")
        cancelar = b2.form_submit_button("Cancelar", width="stretch") if editando else False
    if cancelar:
        ss.editar_agricultor = None
        st.rerun()
    if guardar:
        datos = {"nombre": nombre, "documento": documento, "comunidad": comunidad, "telefono": telefono, "correo": correo}
        try:
            a = parcelas.editar_agricultor(editando.id_agricultor, datos) if editando else parcelas.registrar_agricultor(datos)
        except parcelas.DatosInvalidos as e:
            for err in e.errores:
                st.error(err)
            return
        ss.editar_agricultor = None
        st.success(f"{a.nombre} guardado.", icon=":material/check_circle:")
        if not editando:
            ir("registro", agricultor_id=a.id_agricultor, parcela_id=None, editar_id=None)
        st.rerun()
