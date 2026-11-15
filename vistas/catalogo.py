"""Catálogo de cultivos y reglas agronómicas (actores: especialista agrícola, administrador)."""
import pandas as pd
import streamlit as st

from modules import historial, motor_agronomico as motor
from modules.parcelas import DatosInvalidos
from ui import theme
from vistas.comun import encabezado

FAMILIAS = ["Solanáceas", "Leguminosas", "Gramíneas", "Aliáceas", "Amarantáceas", "Apiáceas", "Baseláceas",
            "Oxalidáceas", "Brasicáceas", "Asteráceas", "Abono verde", "Otra"]


def mostrar():
    encabezado("Catálogo de cultivos y reglas", "Base de conocimiento agronómico usada por el motor de recomendaciones", miga="Vista técnica", icono_miga="capas")
    st.caption("Valores referenciales que deben validar los integrantes de agroindustria y ambiental (RN-10). "
               "Edita rendimiento, precio y costo con datos del mercado local.")
    cat = historial.catalogo()
    df = pd.DataFrame([{"id_cultivo": c["id_cultivo"], "Cultivo": f"{c['emoji']} {c['nombre']}", "Familia": c["familia"],
                        "Ciclo (meses)": c["ciclo_meses"], "Agua": c["necesidad_hidrica"], "Altitud": f"{c['altitud_min']}–{c['altitud_max']}",
                        "N necesita": c["n_demanda_kg_ha"], "N deja": c["n_aporte_kg_ha"], "Rend. t/ha": c["rendimiento_t_ha"],
                        "Precio $/kg": c["precio_usd_kg"], "Costo $/ha": c["costo_usd_ha"]} for c in cat])
    editado = st.data_editor(df, hide_index=True, width="stretch", column_config={"id_cultivo": None},
                             disabled=["Cultivo", "Familia", "Ciclo (meses)", "Agua", "Altitud", "N necesita", "N deja"], key="editor_cat")
    if st.button("Guardar cambios de precios y rendimientos", icon=":material/save:", type="primary"):
        for _, f in editado.iterrows():
            historial.actualizar_parametros(int(f["id_cultivo"]), {"rendimiento_t_ha": float(f["Rend. t/ha"]),
                                                                  "precio_usd_kg": float(f["Precio $/kg"]), "costo_usd_ha": float(f["Costo $/ha"])})
        for k in [k for k in st.session_state if k.startswith(("res_", "prep_"))]:
            del st.session_state[k]
        st.success("Catálogo actualizado.", icon=":material/check_circle:")

    with st.expander("Registrar un cultivo nuevo", icon=":material/add_circle:"):
        with st.form("nuevo_cultivo", clear_on_submit=True):
            c = st.columns(4)
            nombre = c[0].text_input("Nombre")
            emoji = c[1].text_input("Icono", "🌱")
            familia = c[2].selectbox("Familia", FAMILIAS)
            color = c[3].color_picker("Color", "#6a8f4e")
            c = st.columns(4)
            ciclo = c[0].number_input("Ciclo (meses)", 2, 12, 5)
            kc = c[1].number_input("Kc promedio", 0.4, 1.2, 0.8, 0.05)
            amin = c[2].number_input("Altitud mín. (m)", 0, 5000, 2500)
            amax = c[3].number_input("Altitud máx. (m)", 0, 5000, 3300)
            c = st.columns(4)
            hel = c[0].slider("Tolerancia a helada", 0.0, 3.0, 1.0, 0.5)
            seq = c[1].slider("Tolerancia a sequía", 0.0, 3.0, 1.0, 0.5)
            nd = c[2].number_input("N que necesita (kg/ha)", 0, 300, 60)
            nf = c[3].number_input("N que deja (kg/ha)", 0, 150, 0)
            c = st.columns(4)
            cob = c[0].slider("Cobertura del suelo", 0, 3, 2)
            res_ = c[1].slider("Residuos", 0, 3, 1)
            lab = c[2].slider("Laboreo", 0, 3, 1)
            agua = c[3].selectbox("Necesidad de agua", ["baja", "media", "alta"], 1)
            c = st.columns(5)
            phmin = c[0].number_input("pH mín.", 3.5, 9.0, 6.0, 0.1)
            phmax = c[1].number_input("pH máx.", 4.0, 9.5, 7.5, 0.1)
            rend = c[2].number_input("Rendimiento t/ha", 0.1, 100.0, 3.0, 0.1)
            precio = c[3].number_input("Precio $/kg", 0.01, 20.0, 0.5, 0.01)
            costo = c[4].number_input("Costo sin N $/ha", 0, 20000, 1000, 50)
            desc = st.text_input("Nota agronómica")
            if st.form_submit_button("Registrar cultivo", type="primary"):
                if not nombre.strip() or amax <= amin or phmax <= phmin:
                    st.error("Revisa el nombre y que los máximos sean mayores que los mínimos.")
                else:
                    try:
                        historial.registrar_cultivo_personalizado({
                            "nombre": nombre.strip(), "emoji": emoji or "🌱", "familia": familia, "ciclo_meses": int(ciclo), "kc": kc,
                            "necesidad_hidrica": agua, "altitud_min": amin, "altitud_max": amax, "tolerancia_helada": hel, "tolerancia_sequia": seq,
                            "n_demanda_kg_ha": nd, "n_aporte_kg_ha": nf, "cobertura": cob, "residuos": res_, "laboreo": lab, "ph_min": phmin, "ph_max": phmax,
                            "sensible_encharcamiento": False, "rendimiento_t_ha": rend, "precio_usd_kg": precio, "costo_usd_ha": costo, "color": color,
                            "descripcion": desc, "estado_validacion": "registrado por el usuario - pendiente de validación"})
                        st.success(f"{nombre} registrado.", icon=":material/check_circle:")
                    except DatosInvalidos as e:
                        st.error(e.errores[0])

    theme.subtitulo_icono("escudo", "Restricciones agronómicas esenciales (se aplican antes de puntuar)")
    st.dataframe(pd.DataFrame([{"Id": r["id"], "Regla": r["nombre"], "Descripción": r["descripcion"], "Validación": r["estado_validacion"]}
                               for r in motor.REGLAS["restricciones"]]), hide_index=True, width="stretch")
    st.caption("Se editan en data/reglas_agronomicas.json.")
