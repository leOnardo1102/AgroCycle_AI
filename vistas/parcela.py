"""Vista de una parcela: diagnóstico (9.2), historial (CU-02), planes (9.3, CU-03), comparación (9.4, CU-04),
simulador (CU-05), planes guardados (RF-16) y datos técnicos satelitales con fusión multiescala."""
from datetime import date
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from modules import datos_ambientales as amb
from modules import historial, parcelas, recomendaciones as rec
from modules import motor_agronomico as motor
from modules import simulador
from modules.simulador import AVISO, ESCENARIOS
from services import ndvi as ndvi_srv
from ui import theme
from utils.calculos import MESES, MESES_L
from utils.validaciones import AGUA, PROBLEMAS, TEXTURAS
from vistas.comun import confianza_html, encabezado, es_tecnica, fmt, ir, mapa, meses_texto

EQUIPO = ["papa", "haba", "frejol", "maiz", "cebolla"]
EQUIPO_ANUAL = ["papa", "maiz", "quinua", "haba", "arveja", "cebada", "avena", "pasto"]  # 8 cultivos andinos
NOMBRE_CRIT = {"suelo": "Suelo", "agua": "Agua", "clima": "Clima", "sanidad": "Sanidad"}


def _corto(c):
    return c["nombre"].split(" (")[0]


def _prep(p, forzar=False):
    k = f"prep_{p.id_parcela}"
    if forzar or k not in st.session_state:
        with st.spinner("Consultando datos satelitales NASA y propiedades de suelo..."):
            st.session_state[k] = rec.preparar(p, rec.Opciones(), forzar)
    return st.session_state[k]


def mostrar(id_parcela: int):
    p = parcelas.obtener(id_parcela)
    if p is None:
        ir("inicio")
    prep = _prep(p)
    cl, su = prep["clima"], prep["suelo"]
    ndvi_d = cl.get("ndvi")

    c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
    with c1:
        encabezado(
            p.nombre,
            f"{fmt(p.superficie, 2)} ha · {AGUA[p.disponibilidad_agua]} · {p.latitud:.4f}, {p.longitud:.4f}"
            + (" · Problemas: " + ", ".join(PROBLEMAS[x].split(" (")[0].lower() for x in p.lista_problemas) if p.lista_problemas else ""),
            miga="Parcela",
            icono_miga="hoja",
        )
    if c2.button("Editar parcela", icon=":material/edit:", width="stretch"):
        ir("registro", editar_id=p.id_parcela)

    if es_tecnica():
        cuarto_kpi = (
            "NDVI promedio",
            f"{fmt(ndvi_d['ndvi_promedio'], 2)}" if ndvi_d else "—",
            f"actual {fmt(ndvi_d['ndvi_actual'], 2)} · {len(ndvi_d['meses_suelo_desnudo'])} m críticos" if ndvi_d else "sin serie",
            "hoja",
            "#16A34A",
        )
    else:
        hay_desnudo = bool(ndvi_d and ndvi_d.get("meses_suelo_desnudo"))
        cuarto_kpi = (
            "Cobertura en verano",
            "Suelo descubierto" if hay_desnudo else "Buena cobertura",
            "conviene cultivo de cobertura" if hay_desnudo else "protegida todo el año",
            "hoja",
            "#D97706" if hay_desnudo else "#16A34A",
        )

    theme.kpis([
        ("Superficie", f"{fmt(p.superficie, 2)} ha", f"≈ {fmt(p.superficie / 0.7, 1)} cuadras", "capas", theme.VERDE),
        ("Altitud y pendiente", f"{fmt(cl['altitud'])} m", f"Pendiente {fmt(su['pendiente'], 1)} % ({su.get('riesgo_erosion_ladera', 'moderado').replace('_', ' ')})", "montana", "#0E7490"),
        ("Lluvia anual", f"{fmt(cl['lluvia_anual'])} mm", f"Ref. {cl['canton']}", "lluvia", "#0284C7"),
        cuarto_kpi,
    ])

    nombres = [
        ":material/monitor_heart: Diagnóstico",
        ":material/history: Historial",
        ":material/event_note: Plan de cultivo",
        ":material/compare_arrows: Comparar",
        ":material/science: ¿Qué pasa si…?",
        ":material/folder_open: Planes guardados",
    ]
    if es_tecnica():
        nombres.append(":material/satellite_alt: Datos técnicos")
    tabs = st.tabs(nombres)
    with tabs[0]:
        tab_diagnostico(p)
    with tabs[1]:
        tab_historial(p)
    with tabs[2]:
        tab_plan(p)
    with tabs[3]:
        tab_comparar(p)
    with tabs[4]:
        tab_simulador(p)
    with tabs[5]:
        tab_guardados(p)
    if es_tecnica():
        with tabs[6]:
            tab_tecnico(p)


# ------------------------------------------------------------------ diagnóstico
def tab_diagnostico(p):
    prep = _prep(p)
    for a in prep["amb"]["avisos"]:
        st.warning(a, icon=":material/warning:")
    theme.subtitulo_icono("hoja", "Así está tu terreno")
    diag = amb.diagnostico(p, prep["clima"], prep["suelo"], prep["historial"], sencillo=not es_tecnica())
    cols = st.columns(2)
    for i, d in enumerate(diag):
        cols[i % 2].markdown(
            f"<div class='tarjeta'>{theme.titulo_icono(d['icono'], d['titulo'])}{escape(d['texto'])}</div>",
            unsafe_allow_html=True,
        )
    theme.subtitulo_icono("mapa", "Ubicación de la parcela")
    import json
    st_folium(
        mapa(
            p.latitud,
            p.longitud,
            18,
            json.loads(p.poligono) if p.poligono else None,
            dibujar=False,
            minimapa=False,
            ndvi=es_tecnica(),
            nombre=p.nombre,
        ),
        height=400,
        use_container_width=True,
        key=f"mapa_diag_{p.id_parcela}",
        returned_objects=[],
    )
    f = prep["amb"]["fechas"]
    if es_tecnica():
        st.caption("Fuentes: " + " · ".join(f"{k} ({v:%d/%m/%Y})" if v else f"{k} (no disponible)" for k, v in f.items()))
    else:
        st.caption("Información del clima y relieve de tu terreno actualizada con datos satelitales.")
    b1, b2 = st.columns([1.2, 1]) if not p.poligono else (st.container(), None)
    if b1.button("Actualizar datos satelitales de la parcela", icon=":material/refresh:", width="stretch"):
        _prep(p, forzar=True)
        st.session_state.pop(f"res_{p.id_parcela}", None)
        st.rerun()
    if b2 is not None and b2.button("Dibujar el contorno de este terreno", icon=":material/polyline:", width="stretch"):
        ir("registro", editar_id=p.id_parcela)


# ------------------------------------------------------------------ historial
def tab_historial(p):
    theme.subtitulo_icono("historial", "¿Qué has sembrado en esta parcela?")
    st.caption("Registra al menos los últimos 2 o 3 cultivos, del más antiguo al más reciente. Con esto evitamos repetir plagas (RN-01).")
    hist = historial.listar(p.id_parcela)
    if not hist:
        st.info("Todavía no hay cultivos registrados.", icon=":material/info:")
    for h in hist:
        c = h["cultivo"]
        fs = f"{MESES_L[h['fecha_siembra'].month - 1]} {h['fecha_siembra'].year}" if h["fecha_siembra"] else "fecha no indicada"
        fc = f" → cosecha {MESES_L[h['fecha_cosecha'].month - 1]} {h['fecha_cosecha'].year}" if h["fecha_cosecha"] else ""
        a, b = st.columns([6, 1])
        a.markdown(
            f"<div class='tarjeta'>{c['emoji']} <b>{escape(c['nombre'])}</b> · siembra {fs}{fc}"
            f"{'<br><small>' + escape(h['observaciones']) + '</small>' if h['observaciones'] else ''}</div>",
            unsafe_allow_html=True,
        )
        if b.button("", icon=":material/delete:", key=f"delh_{h['id_historial']}", help="Eliminar este registro"):
            historial.eliminar(h["id_historial"])
            st.session_state.pop(f"prep_{p.id_parcela}", None)
            st.rerun()
    with st.form("form_hist", clear_on_submit=True):
        theme.subtitulo_icono("brote", "Agregar un cultivo anterior")
        cat = historial.catalogo()
        c = st.selectbox("Cultivo", cat, format_func=lambda x: f"{x['emoji']} {x['nombre']}")
        hoy = date.today()
        anios = list(range(hoy.year, hoy.year - 6, -1))
        a1, a2, a3, a4 = st.columns(4)
        ms = a1.selectbox("Mes de siembra", range(12), format_func=lambda i: MESES_L[i].capitalize(), index=max(hoy.month - 7, 0))
        ys = a2.selectbox("Año de siembra", anios, index=0 if hoy.month > 6 else 1)
        mc = a3.selectbox("Mes de cosecha", [None] + list(range(12)), format_func=lambda i: "No sé / aún no" if i is None else MESES_L[i].capitalize())
        yc = a4.selectbox("Año de cosecha", anios)
        obs = st.text_input("Observaciones (opcional)", placeholder="Ej. salió con gusano blanco")
        if st.form_submit_button("Agregar", type="primary"):
            datos = {
                "id_cultivo": c["id_cultivo"],
                "fecha_siembra": date(ys, ms + 1, 1),
                "fecha_cosecha": date(yc, mc + 1, 1) if mc is not None else None,
                "observaciones": obs or None,
            }
            try:
                historial.agregar(p.id_parcela, datos)
            except parcelas.DatosInvalidos as e:
                for err in e.errores:
                    st.error(err)
            else:
                st.session_state.pop(f"prep_{p.id_parcela}", None)
                st.session_state.pop(f"res_{p.id_parcela}", None)
                st.rerun()


# ------------------------------------------------------------------ plan de cultivo
TIPOS = {"anual": "Plan de 12 meses (3 etapas)", "rotacion": "Rotación larga (3 o 4 cultivos, 2 a 3 años)"}


def _opciones_ui(p) -> rec.Opciones:
    cat = historial.catalogo()
    ids = [c["id"] for c in cat]
    por_id = {c["id"]: c for c in cat}
    tipo = st.radio("**Tipo de plan**", list(TIPOS), format_func=TIPOS.get, horizontal=True, key=f"tipo_{p.id_parcela}")
    anual = tipo == "anual"
    if anual:
        e = motor.ETAPAS
        cols = st.columns(3)
        for col, et, ej in zip(cols, e, ("papa, maíz suave, quinua", "arveja, haba tierna, cebada", "avena forrajera, pasto con trébol")):
            col.markdown(
                f"<div class='tarjeta etapa'><b>Etapa {et['n']} · {et['nombre']}</b><br><small>{et['meses']} meses · {et['rol'].lower()}"
                f"<br>Ej.: {ej}</small></div>",
                unsafe_allow_html=True,
            )
    defecto = [k for k in (EQUIPO_ANUAL if anual else EQUIPO) if k in ids]
    mes_def = rec.mes_inicio_sugerido(anual)
    etiqueta = lambda k: f"{por_id[k]['emoji']} {por_id[k]['nombre']}"
    if es_tecnica():
        st.markdown("**Prioridades (pesos de 0 a 5)**")
        criterios = [k for k in motor.CRITERIOS if k != "ingresos"]
        cols = st.columns(len(criterios))
        base = rec.PRIORIDADES["tierra"]["pesos"]
        pesos = {k: cols[i].slider(NOMBRE_CRIT[k], 0, 5, base[k], key=f"w_{k}") for i, k in enumerate(criterios)}
        a, b, c, d = st.columns(4)
        n = a.selectbox("Ciclos en la rotación", [3, 4], index=1, disabled=anual, help="Solo para la rotación larga")
        mes = b.selectbox("Mes 1 del plan" if anual else "Mes de inicio", range(12), index=mes_def, key=f"mes_{tipo}",
                          format_func=lambda i: MESES_L[i].capitalize())
        modo = c.selectbox("Lluvia a usar", ["auto", "nasa", "mixta", "local"], format_func={
            "auto": "Automático", "nasa": "NASA POWER", "mixta": "Promedio NASA + local", "local": "Calibrada a la referencia local"}.get)
        leg = d.checkbox("Exigir una leguminosa (R06)", value=True)
        sel = st.multiselect("Cultivos que puede sembrar", ids, default=defecto, format_func=etiqueta, key=f"cult_{tipo}")
        return rec.Opciones(pesos=pesos, n_ciclos=n, cultivos=sel, mes_inicio=mes, exigir_leguminosa=leg, modo_lluvia=modo, tipo=tipo)
    pr = st.radio("**¿Qué es lo más importante para ti?**", list(rec.PRIORIDADES), horizontal=True,
                  format_func=lambda k: rec.PRIORIDADES[k]["nombre"])
    sel = st.multiselect("**¿Qué cultivos puedes sembrar?**", ids, default=defecto, format_func=etiqueta, key=f"cult_{tipo}")
    mes = st.selectbox("**¿Cuándo empiezas a sembrar?**" + (" (inicio de lluvias)" if anual else ""), range(12), index=mes_def,
                       key=f"mes_{tipo}", format_func=lambda i: MESES_L[i].capitalize())
    return rec.Opciones(pesos=dict(rec.PRIORIDADES[pr]["pesos"]), cultivos=sel, mes_inicio=mes, tipo=tipo)


def _anio_inicio(mes_inicio: int) -> int:
    hoy = date.today()
    return hoy.year + (1 if mes_inicio < hoy.month - 1 else 0)


def _tarjeta_testigo(vs: dict, sc_plan: dict, tecnico: bool):
    """Muestra el escenario testigo («Manejo Actual / Sin Rotación») y cuánto mejora el plan elegido."""
    if not vs:
        return
    cult = escape(vs["cultivo_testigo"])
    if tecnico:
        st.markdown(
            f"<div class='testigo-card ok'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap'>"
            f"<div><b style='color:#0F172A'>Comparación vs. Escenario Testigo (Sin rotación: repetir {cult.lower()})</b>"
            f"<div style='color:#334155;font-size:.9rem;margin-top:3px'>{escape(vs['resumen_tecnico'])}</div></div>"
            f"{theme.insignia('Mejora +' + fmt(vs['mejora_suelo_pct']) + '% suelo', 'ok')}</div>"
            f"<div style='margin-top:8px;display:flex;flex-wrap:wrap;gap:10px;font-size:.82rem;color:#475569'>"
            f"<span><b>Testigo suelo:</b> {vs['suelo_testigo']:.0f}/100 → <b>Plan:</b> {sc_plan['suelo']:.0f}/100</span>"
            f"<span><b>Testigo sanidad:</b> {vs['sanidad_testigo']:.0f}/100 → <b>Plan:</b> {sc_plan['sanidad']:.0f}/100</span>"
            f"<span><b>Testigo agua:</b> {vs['agua_testigo']:.0f}/100 → <b>Plan:</b> {sc_plan['agua']:.0f}/100</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='testigo-card ok'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap'>"
            f"<div><b style='color:#0F172A'>Si repites {cult.lower()} todo el año vs. este plan recomendado</b>"
            f"<div style='color:#166534;font-weight:600;font-size:.95rem;margin-top:3px'>{escape(vs['resumen_sencillo'])}</div></div>"
            f"{theme.insignia('Plan superior al manejo actual', 'ok')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def _bloques_evidencia_y_campo(respaldo: list[str], validar: list[str]):
    """Dos bloques claros: Respaldo Satelital NASA y Limitaciones / Qué Validar en Campo."""
    c_sat, c_cam = st.columns(2, gap="medium")
    with c_sat:
        items_sat = "".join(f"<li>{escape(x)}</li>" for x in respaldo)
        st.markdown(
            f"<div class='bloque-info'><h4>{theme.icono('satelite', 18, theme.VERDE_OSC, 2.1)}"
            f"Respaldo Satelital NASA</h4><ul>{items_sat}</ul></div>",
            unsafe_allow_html=True,
        )
    with c_cam:
        items_cam = "".join(f"<li>{escape(x)}</li>" for x in validar)
        st.markdown(
            f"<div class='bloque-info'><h4>{theme.icono('ojo', 18, theme.AMBAR, 2.1)}"
            f"Limitaciones y Qué Validar en Campo</h4><ul>{items_cam}</ul></div>",
            unsafe_allow_html=True,
        )


def tab_plan(p):
    ss = st.session_state
    op = _opciones_ui(p)
    if len(op.cultivos or []) < 3:
        st.warning("Elige al menos 3 cultivos.", icon=":material/warning:")
        return
    if st.button("Generar mi plan de cultivo", icon=":material/auto_awesome:", type="primary", width="stretch"):
        _prep(p)
        with st.spinner("Probando todas las combinaciones de cultivos…"):
            ss[f"res_{p.id_parcela}"] = rec.generar(p.id_parcela, op)
            ss[f"alt_{p.id_parcela}"] = 0
    res = ss.get(f"res_{p.id_parcela}")
    if not res:
        st.info("Elige tus opciones y presiona **Generar mi plan de cultivo**.", icon=":material/info:")
        return
    for a in res["avisos"]:
        st.warning(a, icon=":material/warning:")
    if res["sin_resultado"]:
        if res.get("etapas_sin_cultivo"):
            st.error("Para el plan de 12 meses falta al menos un cultivo para: **" + ", ".join(res["etapas_sin_cultivo"]) +
                     "**. Agrega por ejemplo arveja o cebada (salida de lluvias) y avena forrajera o pasto (verano).", icon=":material/error:")
        else:
            st.error("No hay ninguna combinación que cumpla las restricciones agronómicas esenciales con los cultivos elegidos "
                     f"a {fmt(res['prep']['clima']['altitud'])} m. Prueba agregando más cultivos (por ejemplo haba, arveja o chocho).", icon=":material/error:")
        if res["excluidos_altitud"]:
            st.caption("No se dan a esta altura: " + ", ".join(c["nombre"] for c in res["excluidos_altitud"]))
        return

    alts = res["alternativas"]
    i = st.radio(
        "Alternativas",
        range(len(alts)),
        horizontal=True,
        key=f"alt_{p.id_parcela}",
        format_func=lambda j: f"{'Recomendada · ' if j == 0 else ''}Opción {alts[j]['nombre']}: " + " → ".join(c["emoji"] for c in alts[j]["secuencia"]),
    )
    a = alts[i]
    if es_tecnica():
        mostrar_alternativa(p, res, a)
    else:
        mostrar_guia(a["guia"], a)
    st.divider()
    centro_entrega(p, a["guia"], f"{p.id_parcela}_{a['nombre']}")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Guardar estas alternativas en el historial de planes", icon=":material/bookmark_add:", width="stretch"):
        rec.guardar(res, ss.get("tecnico_id"))
        st.success("Plan guardado. Lo encuentras en la pestaña «Planes guardados».", icon=":material/check_circle:")
    filas = rec.resumen_ciclos(a, p.superficie, res["prep"]["ctx"].mes_inicio, _anio_inicio(res["prep"]["ctx"].mes_inicio))
    csv = pd.DataFrame([
        {
            "cultivo": f["cultivo"]["nombre"],
            "siembra": f["siembra"],
            "cosecha": f["cosecha"],
            "quintales": round(f["quintales"]),
            "urea_sacos_50kg": round(f["urea_sacos"], 1),
            "riego_m3": round(f["riego_m3"]),
        }
        for f in filas
    ])
    c2.download_button(
        "Descargar este plan (CSV)",
        csv.to_csv(index=False).encode("utf-8-sig"),
        f"plan_{p.nombre}_{a['nombre']}.csv",
        "text/csv",
        width="stretch",
        icon=":material/download:",
    )


def mostrar_guia(g: dict, a: dict):
    """Vista agricultor: semáforos, comparación testigo y 4 respuestas prácticas, sin tecnicismos."""
    luces = "".join(f"<div class='luz'><span>{s['luz']}</span><b>{escape(s['titulo'])}</b><small>{escape(s['texto'])}</small></div>" for s in g["semaforos"])
    dur = "12 meses" if g.get("anual") else f"{fmt(g['anios'], 1)} años"
    st.markdown(
        f"<div class='tarjeta verde'><h3>Opción {escape(a['nombre'])} · {dur} · {escape(g.get('periodo', ''))}</h3>"
        f"<div style='font-size:1.15rem'>{escape(g['orden'])}</div><div class='luces'>{luces}</div></div>",
        unsafe_allow_html=True,
    )
    if g.get("vs_testigo"):
        _tarjeta_testigo(g["vs_testigo"], a.get("puntajes", {"suelo": 80, "sanidad": 80, "agua": 80}), tecnico=False)

    theme.subtitulo_icono("calendario", g.get("titulo_pasos", "Qué sembrar, en orden"))
    for paso in g["pasos"]:
        etapa = f"<div class='et'>{escape(paso['etapa'])}</div>" if paso.get("etapa") else ""
        st.markdown(
            f"<div class='ciclo' style='--c:{paso['color']}'>{etapa}"
            f"<h4>{escape(paso['orden'])} · {paso['emoji']} {escape(paso.get('nombre_completo', paso['cultivo']))}</h4>"
            f"Siembra: <b>{escape(paso['siembra'])}</b> → Cosecha: <b>{escape(paso['cosecha'])}</b><br>"
            f"<span class='cifra'><small>Cosecha esperada</small><b>{escape(paso['cantidad'])}</b></span>"
            f"<br>{escape(paso['abono'])}<br><b>Consejo:</b> {escape(paso['consejo'])}"
            + "".join(f"<br><span class='alerta'><b>Atención:</b> {escape(t)}</span>" for t in paso["alertas"])
            + "</div>",
            unsafe_allow_html=True,
        )
    c1, c2, c3 = st.columns(3)
    for col, ic_n, titulo, items in (
        (c1, "check", "Por qué te conviene", g["por_que"]),
        (c2, "tendencia", "Ahorro de agua y dinero", g["ahorro"]),
        (c3, "lluvia", "Cuidados del clima", g["clima"]),
    ):
        with col:
            theme.subtitulo_icono(ic_n, titulo)
            for t in items:
                st.markdown(f"- {t}")

    if g.get("respaldo_nasa") or g.get("validar_campo"):
        _bloques_evidencia_y_campo(g.get("respaldo_nasa", []), g.get("validar_campo", []))

    if g.get("mejorar"):
        st.caption("Para que el plan sea más exacto: " + " ".join(g["mejorar"]))


def _iframe(contenido: str, height: int):
    """HTML con JavaScript propio (no viene del usuario: los datos van escapados). st.iframe en Streamlit nuevo."""
    if hasattr(st, "iframe"):
        st.iframe(contenido, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(contenido, height=height)


def centro_entrega(p, g: dict, clave: str, mensaje_en_expander: bool = True):
    """Centro de Entrega al Agricultor: WhatsApp, correo, hoja para imprimir y PDF."""
    import json as _json

    from modules import entrega, tecnicos
    ag = parcelas.obtener_agricultor(p.id_agricultor)
    tecnico = tecnicos.obtener(st.session_state.get("tecnico_id"))
    theme.subtitulo_icono("enviar", "Entregar el plan al agricultor")
    if tecnico:
        st.caption(f"Firma: **{tecnico.firma}**" + (f" · {tecnico.contacto}" if tecnico.contacto else ""))
    else:
        st.caption("Elige o registra tu perfil en «Mi perfil de técnico» para que tus datos salgan en la hoja, el PDF y los mensajes.")
    msg = entrega.mensaje_whatsapp(g, ag, p, tecnico)
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("Enviar por WhatsApp", entrega.url_whatsapp(ag.telefono, msg), type="primary", width="stretch", icon=":material/chat:")
    c2.link_button("Enviar por correo", entrega.url_correo(ag.correo, p, entrega.texto_plano(g, ag, p, tecnico)), width="stretch", icon=":material/mail:")
    with c3:
        doc = entrega.html_cartilla(g, ag, p, tecnico, imprimir=True)
        _iframe(
            "<button id='b' style='width:100%;height:40px;border:1px solid #CBD5E1;border-radius:10px;background:#fff;"
            "font:600 14px Inter,sans-serif;cursor:pointer;color:#1E293B'>Imprimir hoja</button>"
            f"<script>const d={_json.dumps(doc).replace('</', '<' + chr(92) + '/')};document.getElementById('b').onclick=()=>{{"
            "const w=window.open('','_blank');if(!w){alert('Permite las ventanas emergentes para imprimir');return;}"
            "w.document.open();w.document.write(d);w.document.close();}</script>",
            height=46,
        )
    try:
        pdf = entrega.pdf_cartilla(g, ag, p, tecnico)
        c4.download_button("Descargar PDF", pdf, f"plan_siembra_{ag.nombre.replace(' ', '_')}.pdf",
                           "application/pdf", width="stretch", key=f"pdf_{clave}", icon=":material/picture_as_pdf:")
    except ImportError:
        c4.warning("Para el PDF instala: pip install fpdf2")
    if not ag.telefono or not ag.correo:
        faltan = " y ".join(x for x, falta in (("celular", not ag.telefono), ("correo", not ag.correo)) if falta)
        titulo = f"Completar contacto de {ag.nombre} ({faltan} sin registrar)"
        caja = st.expander(titulo, expanded=not ag.telefono, icon=":material/contact_phone:") if mensaje_en_expander else st.container(border=True)
        if not mensaje_en_expander:
            caja.markdown(f"**{titulo}**")
        with caja:
            with st.form(f"contacto_{clave}"):
                k1, k2 = st.columns(2)
                tel = k1.text_input("Celular (WhatsApp)", value=ag.telefono or "", placeholder="09XXXXXXXX")
                cor = k2.text_input("Correo electrónico", value=ag.correo or "", placeholder="nombre@correo.com")
                if st.form_submit_button("Guardar contacto", icon=":material/save:", type="primary"):
                    try:
                        parcelas.editar_agricultor(ag.id_agricultor, {
                            "nombre": ag.nombre, "documento": ag.documento,
                            "comunidad": ag.comunidad, "telefono": tel, "correo": cor,
                        })
                    except parcelas.DatosInvalidos as e:
                        for err in e.errores:
                            st.error(err)
                    else:
                        st.rerun()
    if mensaje_en_expander:
        with st.expander("Ver y copiar el mensaje (por si WhatsApp no se abre)", icon=":material/content_copy:"):
            st.code(msg, language=None)
    else:
        st.caption("Mensaje para copiar:")
        st.code(msg, language=None)


def _txt_suelo(v):
    return "Suelo en mejora" if v >= 75 else "Suelo estable" if v >= 55 else "Suelo con desgaste"


def _txt_riesgo(v):
    return "Riesgo climático bajo" if v >= 75 else "Riesgo climático medio" if v >= 55 else "Riesgo climático alto"


def mostrar_alternativa(p, res, a):
    sc, area = a["puntajes"], p.superficie
    mes0 = res["prep"]["ctx"].mes_inicio
    filas = rec.resumen_ciclos(a, area, mes0, _anio_inicio(mes0))
    chips = " → ".join(f"<span class='chip'>{c['emoji']} {escape(_corto(c))}</span>" for c in a["secuencia"])
    tot = f" · Puntaje {a['total']:.0f}/100" if es_tecnica() else ""
    st.markdown(
        f"<div class='tarjeta verde'><h3>Opción {escape(a['nombre'])} · {fmt(a['meses'] / 12, 1)} años{tot}</h3>{chips}"
        f"<br><br>{_txt_suelo(sc['suelo'])} &nbsp;·&nbsp; {_txt_riesgo(sc['clima'])} &nbsp;·&nbsp; {confianza_html(a['confianza'])}</div>",
        unsafe_allow_html=True,
    )

    _tarjeta_testigo(a.get("vs_testigo"), sc, tecnico=True)

    theme.subtitulo_icono("calendario", "Calendario técnico de rotación, paso a paso")
    for n, f in enumerate(filas, 1):
        c = f["cultivo"]
        alertas = []
        if f["meses_helada"]:
            alertas.append(f"Riesgo de heladas en {meses_texto(f['meses_helada'])}")
        if f["meses_secos"] and p.disponibilidad_agua != "secano":
            alertas.append(f"Priorizar riego en {meses_texto(f['meses_secos'])}")
        elif f["meses_secos"]:
            alertas.append(f"Déficit pluviométrico probable en {meses_texto(f['meses_secos'])}")
        x = f["ciclo"]
        if x["n_residual"] >= 30 and f["urea_sacos"] < 0.3:
            abono = f"N residual: {_corto(x['anterior']).lower()} aporta nitrógeno (~{x['n_residual']} kg/ha); casi no requiere urea"
        elif f["urea_sacos"] >= 0.3:
            abono = f"Fertilización N: ~<b>{fmt(f['urea_sacos'], 1)} sacos de urea</b> (50 kg)" + (
                f" (reducido por aporte de {_corto(x['anterior']).lower()})" if x["n_residual"] >= 30 else ""
            )
        else:
            abono = "Fertilización N: requerimiento mínimo de urea"
        st.markdown(
            f"<div class='ciclo' style='--c:{c['color']}'><h4>{n}. {c['emoji']} {escape(_corto(c))}</h4>"
            f"Siembra: <b>{escape(f['siembra'])}</b> → Cosecha: <b>{escape(f['cosecha'])}</b><br>"
            f"<span class='cifra'><small>Cosecha esperada</small><b>{fmt(f['quintales'])} quintales</b></span>"
            f"<span class='cifra'><small>Rendimiento</small><b>{fmt(f['rend_t_ha'], 1)} t/ha ({x['rendimiento_rel']:.0%})</b></span>"
            f"<br>{abono}" + "".join(f"<br><span class='alerta'><b>Alerta:</b> {escape(t)}</span>" for t in alertas) + "</div>",
            unsafe_allow_html=True,
        )

    e = a["explicacion"]
    c1, c2, c3 = st.columns(3)
    with c1:
        theme.subtitulo_icono("check", "Por qué y ventajas")
        for t in e["motivos"][:2] + e["ventajas"]:
            st.markdown(f"- {t}")
    with c2:
        theme.subtitulo_icono("alerta", "Limitaciones agronómicas", theme.AMBAR)
        for t in e["limitaciones"]:
            st.markdown(f"- {t}")
    with c3:
        theme.subtitulo_icono("herramienta", "Condiciones de manejo", "#0E7490")
        for t in e["condiciones"] or ["Nada adicional al manejo habitual."]:
            st.markdown(f"- {t}")

    _bloques_evidencia_y_campo(e.get("respaldo_satelital", []), e.get("validar_en_campo", []))

    with st.expander(f"Nivel de confianza: {a['confianza']['nivel']} — información faltante o estimada", icon=":material/info:"):
        for t in a["confianza"]["faltante"]:
            st.markdown(f"- {t}")
        for t in res["notas_pesos"]:
            st.markdown(f"- {t}")
        st.caption("Los resultados son estimaciones orientativas, no garantías de rendimiento ni de precio (RNF-12).")
    _detalle_tecnico(res, a)


def _detalle_tecnico(res, a):
    theme.subtitulo_icono("grafico", "Detalle técnico de simulación")
    criterios = [k for k in motor.CRITERIOS if k != "ingresos"]
    cols = st.columns(len(criterios))
    for i, k in enumerate(criterios):
        cols[i].metric(NOMBRE_CRIT[k], f"{a['puntajes'][k]:.0f}/100")
    linea = []
    for x in a["ciclos"]:
        for j, l in enumerate(x["linea"]):
            linea.append({"n": x["inicio"] + j, "mes": MESES[l["mes"]], "cultivo": _corto(x["cultivo"]), **l})
    df = pd.DataFrame(linea)
    fig = go.Figure()
    fig.add_bar(x=df["n"], y=df["lluvia"], name="Lluvia (mm)", marker_color="#a9cbe6", customdata=df[["mes", "cultivo"]],
                hovertemplate="%{customdata[0]} · %{customdata[1]}<br>Lluvia %{y:.0f} mm<extra></extra>")
    fig.add_bar(x=df["n"], y=df["riego"], name="Riego necesario (mm)", marker_color="#c98b2b")
    fig.add_scatter(x=df["n"], y=df["demanda"], name="Demanda del cultivo (mm)", mode="lines+markers", line=dict(color="#1f2a1f"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), barmode="overlay", legend=dict(orientation="h", y=1.15),
                      xaxis=dict(tickvals=df["n"], ticktext=df["mes"]), yaxis_title="mm/mes")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(pd.DataFrame([{
        "Cultivo": x["cultivo"]["nombre"], "Inicio (mes)": x["inicio"], "Demanda mm": round(x["demanda"]),
        "Lluvia usada mm": round(x["lluvia"]), "Riego mm": round(x["riego"]), "Déficit mm": round(x["deficit"]),
        "f agua": round(x["f_agua"], 2), "f helada": round(x["f_helada"], 2), "f altitud": round(x["f_alt"], 2),
        "f pH": round(x["f_ph"], 2), "f rotación": round(x["f_rot"], 2), "N residual": x["n_residual"],
        "N a aplicar": round(x["n_aplicar"]),
    } for x in a["ciclos"]]), hide_index=True, width="stretch")
    with st.expander("Trazabilidad: datos y reglas usadas (RNF-10)", icon=":material/fact_check:"):
        st.markdown(f"- Secuencias válidas evaluadas: **{fmt(res['evaluadas'])}** · descartadas por restricciones: **{fmt(res['descartadas'])}**")
        st.markdown("- Restricciones esenciales verificadas (todas cumplidas): " + ", ".join(f"{r['id']} {r['nombre']}" for r in motor.REGLAS["restricciones"]))
        st.markdown("- Pesos usados: " + ", ".join(f"{NOMBRE_CRIT[k]} {v}" for k, v in res["pesos"].items() if k in NOMBRE_CRIT))
        cl = res["prep"]["clima"]
        st.markdown(f"- Clima: {cl['fuente']}" + (f" (celda a {fmt(cl['elev_celda'])} m; temperatura corregida {cl['correccion_t']:+.1f} °C; lluvia modo «{cl['modo_lluvia']}»)" if cl.get("elev_celda") else ""))
        st.markdown(f"- Altitud: {fmt(cl['altitud'])} m ({cl['fuente_altitud']}) · Suelo: " +
                    ", ".join(f"{k} = {res['prep']['suelo'][k]} ({v})" for k, v in res["prep"]["suelo"]["fuentes"].items()))
        if res["excluidos_altitud"]:
            st.markdown("- Excluidos por altitud (R05): " + ", ".join(c["nombre"] for c in res["excluidos_altitud"]))


# ------------------------------------------------------------------ comparación
def tab_comparar(p):
    res = st.session_state.get(f"res_{p.id_parcela}")
    if not res or res["sin_resultado"]:
        st.info("Primero genera un plan en la pestaña «Plan de cultivo».", icon=":material/info:")
        return
    alts = res["alternativas"]
    testigo = res.get("testigo")
    theme.subtitulo_icono("radar", "Compara las opciones frente al manejo sin rotación")
    criterios = [k for k in motor.CRITERIOS if k in NOMBRE_CRIT]
    cats = [NOMBRE_CRIT[k] for k in criterios]
    fig = go.Figure()
    colores = ["#15803D", "#0284C7", "#7C3AED"]
    for j, a in enumerate(alts):
        vals = [a["puntajes"][k] for k in criterios]
        fig.add_trace(go.Scatterpolar(
            r=vals + vals[:1], theta=cats + cats[:1],
            name=f"Opción {a['nombre']}", fill="toself",
            line=dict(color=colores[j % len(colores)]), opacity=0.55,
        ))
    if testigo:
        vals_t = [testigo["puntajes"][k] for k in criterios]
        fig.add_trace(go.Scatterpolar(
            r=vals_t + vals_t[:1], theta=cats + cats[:1],
            name=f"Testigo (repetir {testigo['nombre_cultivo'].lower()})",
            line=dict(color="#D97706", dash="dash", width=2.5),
        ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=420, margin=dict(l=40, r=40, t=30, b=30))
    st.plotly_chart(fig, width="stretch")

    criterios = [k for k in motor.CRITERIOS if k != "ingresos"]
    filas_comp = []
    if testigo:
        filas_comp.append({
            "Opción": "Testigo (Sin rotación)",
            "Cultivos": " → ".join(c["emoji"] + " " + _corto(c) for c in testigo["secuencia"]),
            **{NOMBRE_CRIT[k]: round(testigo["puntajes"][k]) for k in criterios},
            "Diversidad (familias)": len({c["familia"] for c in testigo["secuencia"]}),
            "Riego (m³)": fmt(testigo["riego_total"] * 10 * p.superficie),
            "Confianza": "Línea base",
        })
    for a in alts:
        filas_comp.append({
            "Opción": f"Opción {a['nombre']}",
            "Cultivos": " → ".join(c["emoji"] + " " + _corto(c) for c in a["secuencia"]),
            **{NOMBRE_CRIT[k]: round(a["puntajes"][k]) for k in criterios},
            "Diversidad (familias)": len({c["familia"] for c in a["secuencia"]}),
            "Riego (m³)": fmt(a["riego_total"] * 10 * p.superficie),
            "Confianza": a["confianza"]["nivel"],
        })
    st.dataframe(pd.DataFrame(filas_comp), hide_index=True, width="stretch")
    st.caption("Los puntajes (0-100) son indicadores comparativos del modelo frente al escenario testigo, no mediciones directas de fertilidad (sección 9.4).")


# ------------------------------------------------------------------ simulador
def tab_simulador(p):
    res = st.session_state.get(f"res_{p.id_parcela}")
    if not res or res["sin_resultado"]:
        st.info("Primero genera un plan en la pestaña «Plan de cultivo».", icon=":material/info:")
        return
    prep = res["prep"]
    smap_data = prep["amb"].get("NASA SMAP")
    gpm_data = prep["clima"].get("gpm")
    diag_smap = simulador.diagnosticar_smap(smap_data)

    theme.subtitulo_icono("tendencia", "¿Qué pasaría si…?")
    st.caption(AVISO)

    if es_tecnica():
        gpm_txt = (
            f"GPM IMERG: {gpm_data['dias_lluvia_intensa_anual']:.0f} días/año de lluvia intensa · lavado {gpm_data['riesgo_lavado']}."
            if gpm_data else ""
        )
        st.markdown(
            f"<div class='tarjeta'><b>Lectura satelital conectada al simulador (NASA SMAP + GPM):</b><br>"
            f"{escape(diag_smap['mensaje_tecnico'])} {escape(gpm_txt)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='tarjeta'><b>Estado actual de humedad de la tierra:</b> "
            f"{escape(diag_smap['mensaje_sencillo'])}</div>",
            unsafe_allow_html=True,
        )

    esc_keys = list(ESCENARIOS)
    def_idx = esc_keys.index(diag_smap["escenario_sugerido"]) if diag_smap["escenario_sugerido"] in esc_keys else 0
    esc = st.radio("Escenario", esc_keys, index=def_idx, horizontal=True, format_func=lambda k: ESCENARIOS[k]["nombre"])
    st.markdown(f"*{ESCENARIOS[esc]['descripcion']}*")
    usar_smap = st.checkbox(
        "Incorporar anomalía de humedad superficial NASA SMAP al inicio de la simulación" if es_tecnica()
        else "Tomar en cuenta la humedad actual de la tierra al inicio",
        value=abs(diag_smap["anomalia_hidrica_pct"]) >= 5.0,
    )
    if st.button("Simular escenario", icon=":material/science:", type="primary"):
        with st.spinner("Recalculando…"):
            st.session_state[f"sim_{p.id_parcela}"] = rec.simular(p.id_parcela, res["opciones"], res, esc, usar_smap=usar_smap)
    sim = st.session_state.get(f"sim_{p.id_parcela}")
    if not sim:
        return
    st.markdown(f"#### Resultado con **{sim['info']['nombre']}** (hipotético)")
    filas = []
    criterios = [k for k in motor.CRITERIOS if k != "ingresos"]
    for f in sim["filas"]:
        b, e = f["base"], f["escenario"]
        filas.append({
            "Opción": f["nombre"],
            "Cultivos": " → ".join(c["emoji"] for c in b["secuencia"]),
            "Puntaje normal": round(b["total"]),
            "Puntaje con escenario": round(e["total"]),
            "Cambio": round(e["total"] - b["total"], 1),
            **({NOMBRE_CRIT[k]: round(e["puntajes"][k] - b["puntajes"][k]) for k in criterios} if es_tecnica() else {}),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    mejor = max(sim["filas"], key=lambda f: f["escenario"]["total"])
    st.success(f"Con este escenario, la opción que mejor resiste es la **Opción {mejor['nombre']}**.", icon=":material/check_circle:")
    m = sim["mejor_en_escenario"]
    if m and [c["id"] for c in m["secuencia"]] not in [[c["id"] for c in f["base"]["secuencia"]] for f in sim["filas"]]:
        st.info("Si este escenario fuera seguro, convendría: " + " → ".join(c["emoji"] + " " + _corto(c) for c in m["secuencia"]) + f" ({m['total']:.0f}/100).", icon=":material/info:")


# ------------------------------------------------------------------ planes guardados
def tab_guardados(p):
    planes = rec.listar_planes(p.id_parcela)
    if not planes:
        st.info("Aún no guardas planes para esta parcela.", icon=":material/info:")
        return
    cat = {c["id"]: c for c in historial.catalogo()}
    for pl in planes:
        seq = " → ".join(cat[k]["emoji"] + " " + _corto(cat[k]) for k in pl["secuencia"] if k in cat)
        with st.expander(f"{pl['fecha']:%d/%m/%Y %H:%M} · {pl['alternativa']} · {seq} · {pl['puntuacion']:.0f}/100 · confianza {pl['confianza'].lower()}"):
            d = pl["detalle"]
            if d.get("guia") and not es_tecnica():
                mostrar_guia(d["guia"], {"nombre": pl["alternativa"].replace("Alternativa ", ""), "puntajes": d.get("puntajes", {})})
            else:
                st.write(pl["justificacion"])
                if d.get("vs_testigo"):
                    _tarjeta_testigo(d["vs_testigo"], d.get("puntajes", {}), tecnico=True)
            from modules import tecnicos
            t = tecnicos.obtener(pl.get("id_tecnico"))
            st.caption(
                f"Fuentes: clima {d['fuentes']['clima']}, altitud {d['fuentes']['altitud']}"
                + (f" · Técnico: {t.firma}" if t else "")
                + (" · Plan de 12 meses" if pl.get("tipo") == "anual" else "")
            )
            if d.get("guia"):
                centro_entrega(p, d["guia"], f"guardado_{pl['id_plan']}", mensaje_en_expander=False)


# ------------------------------------------------------------------ datos técnicos
def tab_tecnico(p):
    prep = _prep(p)
    cl, su = prep["clima"], prep["suelo"]
    ndvi_data = cl.get("ndvi")
    gpm_data = cl.get("gpm")
    smap_data = cl.get("smap")

    theme.subtitulo_icono("satelite", "Datos de observación de la Tierra (NASA + SoilGrids)")
    theme.kpis([
        ("Altitud (SRTM 30 m)", f"{fmt(cl['altitud'])} m", cl["fuente_altitud"], "montana", "#0E7490"),
        ("Pendiente y erosión", f"{fmt(su['pendiente'], 1)} %",
         f"Riesgo {su.get('riesgo_erosion_ladera', 'moderado').replace('_', ' ')} (LS {su.get('factor_ls', 1.0)})", "alerta", "#D97706"),
        ("Lluvia usada / GPM", f"{fmt(cl['lluvia_anual'])} mm/año",
         f"GPM: {gpm_data['dias_lluvia_intensa_anual']:.0f} d intensos · lavado {gpm_data['riesgo_lavado']}" if gpm_data else "Climatología anual",
         "lluvia", "#0284C7"),
        ("NDVI / SMAP actual", f"NDVI {ndvi_data['ndvi_actual']:.2f}" if ndvi_data else "—",
         f"SMAP {smap_data['humedad_superficial_pct']:.0f} % ({smap_data['anomalia_hidrica_pct']:+.1f} %)" if smap_data else "Sin lectura",
         "hoja", "#16A34A"),
    ])

    # Curva estacional NDVI + detección de meses críticos de suelo desnudo
    if ndvi_data:
        theme.subtitulo_icono("hoja", "Serie estacional NDVI (MODIS / Landsat / Sentinel-2) y suelo desnudo")
        curva = ndvi_data["curva_estacional"]
        colores_barra = ["#D97706" if v <= ndvi_srv.UMBRAL_SUELO_DESNUDO else "#16A34A" for v in curva]
        fig_ndvi = go.Figure()
        fig_ndvi.add_bar(x=MESES, y=curva, name="NDVI mensual", marker_color=colores_barra)
        fig_ndvi.add_scatter(x=MESES, y=curva, name="Curva estacional", mode="lines+markers", line=dict(color="#0F291E", width=2.5))
        fig_ndvi.add_hline(y=ndvi_srv.UMBRAL_SUELO_DESNUDO, line_dash="dash", line_color="#DC2626",
                           annotation_text="Umbral suelo desnudo (0,30)")
        fig_ndvi.update_layout(height=280, margin=dict(l=10, r=10, t=25, b=10), yaxis=dict(range=[0.1, 0.9], title="NDVI (0,15–0,85)"))
        st.plotly_chart(fig_ndvi, width="stretch")
        if ndvi_data["meses_suelo_desnudo"]:
            st.warning(ndvi_data["alerta_erosion"], icon=":material/warning:")
        else:
            st.success(ndvi_data["alerta_erosion"], icon=":material/check_circle:")

    # Panel GPM IMERG + SMAP L4
    if gpm_data or smap_data:
        theme.subtitulo_icono("lluvia", "Lluvias intensas (NASA GPM IMERG) y humedad superficial (NASA SMAP)")
        fig_gs = go.Figure()
        if gpm_data:
            fig_gs.add_bar(x=MESES, y=gpm_data["frecuencia_mensual_intensa"], name="GPM días lluvia intensa/mes", marker_color="#0284C7", yaxis="y")
        if smap_data:
            fig_gs.add_scatter(x=MESES, y=[round(v * 100, 1) for v in smap_data["humedad_mensual"]], name="SMAP humedad superficial (%)",
                               mode="lines+markers", line=dict(color="#15803D", width=2.5), yaxis="y2")
        fig_gs.update_layout(
            height=280, margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", y=1.16),
            yaxis=dict(title="Días intensos / mes"), yaxis2=dict(title="Humedad (%)", overlaying="y", side="right", range=[0, 100]),
        )
        st.plotly_chart(fig_gs, width="stretch")
        if gpm_data:
            st.caption(f"GPM IMERG ({gpm_data['resolucion']}): intensidad máx. {gpm_data['intensidad_max_mm_dia']} mm/día, "
                       f"índice erosividad R ≈ {gpm_data['indice_erosividad_r']}. {gpm_data['recomendacion_manejo']}")

    ms = cl["meses"]
    df = pd.DataFrame({
        "Mes": MESES,
        "Lluvia mm": [round(m["p"]) for m in ms],
        "Lluvia efectiva": [round(m["pe"]) for m in ms],
        "ET0 mm": [round(m["et0"]) for m in ms],
        "T media °C": [round(m["t"], 1) for m in ms],
        "T mín °C": [round(m["tmin"], 1) for m in ms],
        "Riesgo helada": [f"{m['fr']:.0%}" for m in ms],
    })
    if cl.get("meses_crudos"):
        df.insert(2, "Lluvia NASA cruda", [round(m["p"]) for m in cl["meses_crudos"]])
        crudo = cl["meses_crudos"]
        st.markdown(f"**Valores exactos de NASA POWER** (celda a {fmt(cl['elev_celda'])} m, sin corregir) · fuente: {cl['fuente']}")
        nasa = pd.DataFrame({
            "Mes": MESES,
            "PRECTOTCORR (mm/mes)": [round(m["p"], 1) for m in crudo],
            "T2M (°C)": [round(m["t"], 2) for m in crudo],
            "T2M_MIN (°C)": [round(m["tmin"], 2) for m in crudo],
            "T2M_MAX (°C)": [round(m["tmax"], 2) for m in crudo],
            "ALLSKY_SFC_SW_DWN (kWh/m²/d)": [round(m["rad"], 2) if m.get("rad") is not None else None for m in crudo],
            "GWETROOT (0-1)": [round(m["gwetroot"], 2) if m.get("gwetroot") is not None else None for m in crudo],
        })
        st.dataframe(nasa, hide_index=True, width="stretch")
        fig = go.Figure()
        fig.add_bar(x=MESES, y=nasa["PRECTOTCORR (mm/mes)"], name="PRECTOTCORR (mm)", marker_color="#a9cbe6", yaxis="y")
        fig.add_scatter(x=MESES, y=nasa["T2M_MAX (°C)"], name="T2M_MAX", line=dict(color="#b5452f"), yaxis="y2")
        fig.add_scatter(x=MESES, y=nasa["T2M (°C)"], name="T2M", line=dict(color="#c98b2b"), yaxis="y2")
        fig.add_scatter(x=MESES, y=nasa["T2M_MIN (°C)"], name="T2M_MIN", line=dict(color="#5d6fb5"), yaxis="y2")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.15),
                          yaxis=dict(title="mm/mes"), yaxis2=dict(title="°C", overlaying="y", side="right"))
        st.plotly_chart(fig, width="stretch")
        st.markdown("**Clima usado por el motor** (temperatura corregida por altitud y lluvia según el modo elegido)")
    st.dataframe(df, hide_index=True, width="stretch")
    st.markdown("**Suelo** · " + " · ".join(f"{k}: **{su[k] if k != 'textura' else TEXTURAS.get(su[k], su[k])}** ({v})" for k, v in su["fuentes"].items()))

    # Tarjeta / Sección obligatoria: Fusión de Datos Satelitales y Escalas
    theme.subtitulo_icono("capas", "Fusión de Datos Satelitales y Escalas")
    st.markdown(
        "<div class='tarjeta'><b>Armonización multiescala al polígono de la parcela:</b> las resoluciones satelitales varían entre "
        "30 m (relieve SRTM) y ~50 km (climatología NASA POWER). AgroCycle AI integra cada fuente reduciendo la escala térmica por "
        "gradiente andino (-0,58 °C/100 m), calibrando lluvia con estaciones cantonales y evaluando la incertidumbre espacial.</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(amb.TABLA_FUSION_ESCALAS), hide_index=True, width="stretch")

    theme.subtitulo_icono("mapa", "Mapa con capas NASA (usa el selector de capas para activar NDVI MODIS)")
    import json
    st_folium(
        mapa(
            p.latitud,
            p.longitud,
            18,
            json.loads(p.poligono) if p.poligono else None,
            dibujar=False,
            minimapa=False,
            ndvi=True,
            nombre=p.nombre,
        ),
        height=380,
        key=f"mapa_tec_{p.id_parcela}",
        use_container_width=True,
        returned_objects=[],
    )
