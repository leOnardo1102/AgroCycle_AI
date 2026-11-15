"""Módulo de inicio (9.1): parcelas registradas, mapa general, indicadores y acceso al registro."""
from html import escape

import streamlit as st
from streamlit_folium import st_folium

from modules import historial, parcelas, recomendaciones
from ui import theme
from vistas.comun import fmt, ir, mapa_general

ESTADOS = {  # clave: (texto de la insignia, tipo de insignia, color en el mapa)
    "plan": ("Con plan de rotación", "ok", "#15803D"),
    "lista": ("Lista para planificar", "lista", "#10B981"),
    "falta": ("Falta el historial", "falta", "#D97706"),
}
AGUA_CORTO = {"completo": "Permanente", "turnos": "Por turnos", "secano": "Solo lluvia"}


def _corto(nombre: str) -> str:
    return nombre.split(" (")[0]


def mostrar():
    ss = st.session_state
    agr = parcelas.obtener_agricultor(ss.agricultor_id)
    lista = parcelas.listar(ss.agricultor_id)
    sub = " · ".join(x for x in [agr.comunidad if agr else None, f"Cel. {agr.telefono}" if agr and agr.telefono else None] if x)
    theme.encabezado(
        f"Parcelas de {agr.nombre}" if agr else "Mis parcelas",
        sub or "Terrenos registrados del agricultor",
        miga="Agricultor",
        icono_miga="usuarios",
    )

    if not lista:
        st.markdown(
            "<div class='tarjeta'><h3>Aún no hay parcelas registradas</h3>Registra el primer terreno marcándolo en el mapa "
            "satelital para recibir un plan de rotación.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Registrar la primera parcela", icon=":material/add_location_alt:", type="primary"):
            ir("registro", editar_id=None)
        return

    cat = {c["id"]: c for c in historial.catalogo()}
    info = []
    for p in lista:
        hist = historial.listar(p.id_parcela)
        planes = recomendaciones.listar_planes(p.id_parcela)
        info.append((p, hist, planes, "plan" if planes else ("lista" if hist else "falta")))

    total = sum(p.superficie for p in lista)
    con_plan = sum(1 for x in info if x[3] == "plan")
    con_riego = sum(1 for p in lista if p.disponibilidad_agua != "secano")
    theme.kpis([
        ("Parcelas", len(lista), "registradas", "mapa", theme.VERDE),
        ("Superficie total", f"{fmt(total, 2)} ha", f"≈ {fmt(total / 0.7, 1)} cuadras", "capas", "#0E7490"),
        ("Con plan de rotación", f"{con_plan} / {len(lista)}",
         "todas planificadas" if con_plan == len(lista) else f"{len(lista) - con_plan} por planificar", "calendario", "#7C3AED"),
        ("Con riego", f"{con_riego} / {len(lista)}", f"{len(lista) - con_riego} solo con lluvia", "gota", "#0284C7"),
    ])

    izq, der = st.columns([1.15, 1], gap="large")
    with izq:
        theme.subtitulo_icono("mapa", "Mapa de las parcelas")
        colores = {p.id_parcela: ESTADOS[e][2] for p, _, _, e in info}
        st_folium(
            mapa_general(lista, colores),
            height=480,
            use_container_width=True,
            key=f"mapa_general_{ss.agricultor_id}_{len(lista)}",
            returned_objects=[],
        )
        st.markdown(
            "<div class='leyenda'>" + "".join(f"<span><i style='background:{c}'></i>{t}</span>" for t, _, c in ESTADOS.values())
            + "<span style='color:#94A3B8'>Haz clic en una parcela para ver su ficha</span></div>",
            unsafe_allow_html=True,
        )
    with der:
        c1, c2 = st.columns([1.3, 1], vertical_alignment="center")
        with c1:
            theme.subtitulo_icono("capas", "Terrenos")
        if c2.button("Nueva parcela", icon=":material/add:", width="stretch"):
            ir("registro", editar_id=None)
        orden = {"falta": 0, "lista": 1, "plan": 2}
        for p, hist, planes, estado in sorted(info, key=lambda x: orden[x[3]]):
            texto, tipo, color = ESTADOS[estado]
            ultimo = f"{hist[-1]['cultivo']['emoji']} {_corto(hist[-1]['cultivo']['nombre'])}" if hist else "Sin registrar"
            if planes:
                pl = planes[0]
                pie = (
                    f"Plan del {pl['fecha']:%d/%m/%Y}: "
                    + " → ".join(cat[k]["emoji"] + " " + _corto(cat[k]["nombre"]) for k in pl["secuencia"] if k in cat)
                )
            elif hist:
                pie = "Tiene historial: ya puedes generar las alternativas de rotación."
            else:
                pie = "Registra qué se sembró antes para obtener un plan confiable."
            st.markdown(
                f"<div class='parcela {estado}' style='--c:{color}'><div class='cab'><h3>{escape(p.nombre)}</h3>"
                f"{theme.insignia(texto, tipo)}</div>"
                f"<div class='datos'><div><small>{theme.icono('capas', 12)}Superficie</small><b>{fmt(p.superficie, 2)} ha</b></div>"
                f"<div><small>{theme.icono('gota', 12)}Agua</small><b>{AGUA_CORTO.get(p.disponibilidad_agua, p.disponibilidad_agua)}</b></div>"
                f"<div><small>{theme.icono('hoja', 12)}Cultivo previo</small><b>{escape(ultimo)}</b></div></div>"
                f"<div class='pie'>{escape(pie)}</div></div>",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns([2, 1])
            if b1.button(
                "Abrir parcela",
                key=f"abrir_{p.id_parcela}",
                icon=":material/arrow_forward:",
                type="primary" if estado == "lista" else "secondary",
                width="stretch",
            ):
                ir("parcela", parcela_id=p.id_parcela)
            if b2.button("Editar", key=f"editar_{p.id_parcela}", icon=":material/edit:", width="stretch"):
                ir("registro", editar_id=p.id_parcela)
