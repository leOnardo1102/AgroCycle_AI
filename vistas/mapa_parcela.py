"""Selector de parcela en el mapa, pensado para que sea fácil marcar y dibujar el terreno.

Formas de hacerlo:
  1. Marcar el centro: un toque en el mapa.
  2. Dibujar tocando las esquinas: cada toque agrega un punto numerado y se une con el anterior; al presionar
     «Confirmar contorno» los puntos se unen en el mismo orden en que se tocaron y se cierra el terreno.
  3. Herramientas del mapa (contorno / rectángulo), con área en hectáreas, edición y borrado.
Además: buscador de lugares, botón «mi ubicación» (GPS), pantalla completa y vista satelital con mucho acercamiento.
Todos los textos del mapa (también los de Leaflet) salen en el idioma elegido (Español / English).
"""
import json

import folium
import streamlit as st
from branca.element import Element, MacroElement
from folium.plugins import Draw, Fullscreen, Geocoder, LocateControl, MousePosition
from jinja2 import Template
from streamlit_folium import st_folium

from modules.datos_ambientales import CANTONES
from ui import theme
from ui.i18n import en_ingles, tr
from utils.calculos import area_poligono_ha
from vistas.comun import capas_base, fmt

TARJETAS_MODO = {  # clave: (título, descripción, icono)
    "esquinas": ("Dibujar el contorno", "Toca las esquinas en orden y presiona «Confirmar contorno»", ":material/polyline:"),
    "punto": ("Marcar solo un punto", "Un toque en el mapa ubica el centro", ":material/location_on:"),
}
AMARILLO = "#facc15"
VERDE_POL = "#22c55e"
NARANJA = "#f97316"
MIN_PUNTOS = 3

# Textos de Leaflet.draw en cada idioma (Leaflet no pasa por la capa de traducción de Streamlit)
DRAW_LOCAL = {
    "es": {
        "cancel_t": "Cancelar el dibujo", "cancel": "Cancelar", "finish_t": "Terminar el dibujo", "finish": "Terminar",
        "undo_t": "Borrar la última esquina", "undo": "Deshacer", "polygon": "Dibujar el contorno de tu terreno",
        "rectangle": "Dibujar un terreno rectangular", "poly_start": "Toca la primera esquina de tu terreno",
        "poly_cont": "Toca la siguiente esquina", "poly_end": "Toca la primera esquina para cerrar, o «Terminar»",
        "rect_start": "Presiona y arrastra para dibujar el rectángulo", "shape_end": "Suelta para terminar",
        "save_t": "Guardar los cambios", "save": "Guardar", "clear_t": "Borrar todo", "clear": "Borrar todo",
        "edit": "Mover las esquinas del dibujo", "edit_off": "No hay nada que editar", "remove": "Borrar el dibujo",
        "remove_off": "No hay nada que borrar", "edit_tip": "Arrastra las esquinas para ajustar el contorno",
        "edit_sub": "Luego toca «Guardar»", "remove_tip": "Toca el dibujo que quieres borrar",
    },
    "en": {
        "cancel_t": "Cancel drawing", "cancel": "Cancel", "finish_t": "Finish drawing", "finish": "Finish",
        "undo_t": "Delete the last corner", "undo": "Undo", "polygon": "Draw the outline of your field",
        "rectangle": "Draw a rectangular field", "poly_start": "Tap the first corner of your field",
        "poly_cont": "Tap the next corner", "poly_end": "Tap the first corner to close it, or “Finish”",
        "rect_start": "Press and drag to draw the rectangle", "shape_end": "Release to finish",
        "save_t": "Save changes", "save": "Save", "clear_t": "Clear all", "clear": "Clear all",
        "edit": "Move the corners of the drawing", "edit_off": "Nothing to edit", "remove": "Delete the drawing",
        "remove_off": "Nothing to delete", "edit_tip": "Drag the corners to adjust the outline",
        "edit_sub": "Then tap “Save”", "remove_tip": "Tap the drawing you want to delete",
    },
}


class DibujoTraducido(MacroElement):
    """Traduce Leaflet.draw al idioma activo y evita conflictos con clics sueltos mientras se usa la barra de dibujo."""
    _template = Template("""{% macro script(this, kwargs) %}
    if (typeof L !== 'undefined' && L.drawLocal) {
      var d = L.drawLocal, t = {{this.textos}};
      d.draw.toolbar.actions.title = t.cancel_t; d.draw.toolbar.actions.text = t.cancel;
      d.draw.toolbar.finish.title = t.finish_t; d.draw.toolbar.finish.text = t.finish;
      d.draw.toolbar.undo.title = t.undo_t; d.draw.toolbar.undo.text = t.undo;
      d.draw.toolbar.buttons.polygon = t.polygon;
      d.draw.toolbar.buttons.rectangle = t.rectangle;
      d.draw.handlers.polygon.tooltip.start = t.poly_start;
      d.draw.handlers.polygon.tooltip.cont = t.poly_cont;
      d.draw.handlers.polygon.tooltip.end = t.poly_end;
      d.draw.handlers.rectangle.tooltip.start = t.rect_start;
      d.draw.handlers.simpleshape.tooltip.end = t.shape_end;
      d.edit.toolbar.actions.save.title = t.save_t; d.edit.toolbar.actions.save.text = t.save;
      d.edit.toolbar.actions.cancel.title = t.cancel_t; d.edit.toolbar.actions.cancel.text = t.cancel;
      d.edit.toolbar.actions.clearAll.title = t.clear_t; d.edit.toolbar.actions.clearAll.text = t.clear;
      d.edit.toolbar.buttons.edit = t.edit; d.edit.toolbar.buttons.editDisabled = t.edit_off;
      d.edit.toolbar.buttons.remove = t.remove; d.edit.toolbar.buttons.removeDisabled = t.remove_off;
      d.edit.handlers.edit.tooltip.text = t.edit_tip;
      d.edit.handlers.edit.tooltip.subtext = t.edit_sub;
      d.edit.handlers.remove.tooltip.text = t.remove_tip;
    }
    var mapaObj = {{this._parent.get_name()}};
    if (mapaObj && !mapaObj.agroDrawHooked) {
      mapaObj.agroDrawHooked = true;
      var drawActivo = false;
      mapaObj.on('draw:drawstart draw:editstart draw:deletestart', function(){ drawActivo = true; });
      mapaObj.on('draw:drawstop draw:editstop draw:deletestop draw:created draw:edited draw:deleted', function(){
        setTimeout(function(){ drawActivo = false; }, 160);
      });
      var origFire = mapaObj.fire;
      mapaObj.fire = function(tipo, datos, prop) {
        if (tipo === 'click' && drawActivo) { return this; }
        return origFire.apply(this, arguments);
      };
    }
    {% endmacro %}""")

    def __init__(self, idioma: str = "es"):
        super().__init__()
        self._name = "DibujoTraducido"
        self.textos = json.dumps(DRAW_LOCAL.get(idioma, DRAW_LOCAL["es"]), ensure_ascii=False)


# Alias por compatibilidad con código anterior
DibujoEnEspanol = DibujoTraducido

CSS = """<style>
.leaflet-draw.leaflet-control{transform:scale(1.3);transform-origin:top left;margin-top:14px!important}
.leaflet-draw-actions a{font-size:13px!important;font-weight:600}
.leaflet-control-locate a,.leaflet-control-fullscreen a{width:38px!important;height:38px!important;line-height:38px!important}
.leaflet-draw-tooltip{font-size:13px!important}
.leaflet-control-geocoder{font-size:14px;border-radius:10px!important;border:0!important;box-shadow:0 2px 10px rgba(0,0,0,.25)!important}
.leaflet-control-geocoder-form input{width:230px;padding:6px 8px}
.agro-vertice{display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
  border:2.5px solid #fff;font:700 12px/1 Inter,system-ui,sans-serif;color:#1f2937;box-shadow:0 2px 6px rgba(0,0,0,.45)}
</style>"""


def _num(x: float, dec: int = 0) -> str:
    """Cifra en el formato del idioma activo (1.234,5 en español · 1,234.5 en inglés)."""
    return f"{x:,.{dec}f}" if en_ingles() else fmt(x, dec)


def _mapa_base(centro, zoom, ndvi: bool) -> folium.Map:
    """Mapa fijo (no cambia entre clics de esquinas) para mantener fluido el acercamiento del usuario."""
    m = folium.Map(location=centro, zoom_start=zoom, tiles=None, control_scale=True, max_zoom=22)
    capas_base(m, ndvi)
    m.get_root().header.add_child(Element(CSS))
    Geocoder(collapsed=False, position="topright", add_marker=False, zoom=18,
             placeholder=tr("Buscar comunidad o lugar…"), error_message=tr("No se encontró ese lugar")).add_to(m)
    LocateControl(position="topleft", flyTo=True, initialZoomLevel=19,
                  strings={"title": tr("Ir a mi ubicación (GPS)"), "popup": tr("Estás aquí")}).add_to(m)
    Fullscreen(position="topleft", title=tr("Pantalla completa"), title_cancel=tr("Salir de pantalla completa")).add_to(m)
    m.add_child(DibujoTraducido("en" if en_ingles() else "es"))
    forma = {"color": AMARILLO, "weight": 3.5, "fillColor": VERDE_POL, "fillOpacity": 0.25}
    Draw(position="topleft", show_geometry_on_click=False,
         draw_options={"polyline": False, "circle": False, "circlemarker": False, "marker": False,
                       "polygon": {"allowIntersection": False, "showArea": True, "metric": ["ha", "m"], "shapeOptions": forma},
                       "rectangle": {"showArea": True, "metric": ["ha", "m"], "shapeOptions": forma}},
         edit_options={"edit": True, "remove": True}).add_to(m)
    MousePosition(position="bottomleft", separator=" , ", prefix=tr("Coord."), num_digits=5, empty_string="").add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    return m


def _poligono_de(vertices: list) -> dict:
    """Polígono GeoJSON que une los puntos en el mismo orden en que se tocaron y vuelve al primero."""
    anillo = [[lon, lat] for lat, lon in vertices]
    return {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [anillo + [anillo[0]]]}}


def _centroide(feature: dict) -> tuple[float, float]:
    anillo = feature["geometry"]["coordinates"][0][:-1] or feature["geometry"]["coordinates"][0]
    return sum(p[1] for p in anillo) / len(anillo), sum(p[0] for p in anillo) / len(anillo)


def _vertices_de(feature: dict | None) -> list:
    if not feature:
        return []
    coords = feature.get("geometry", {}).get("coordinates", [[]])[0]
    anillo = coords[:-1] if len(coords) > 1 and coords[0] == coords[-1] else coords
    return [[p[1], p[0]] for p in anillo]


def _area_vertices(vertices: list) -> float:
    return area_poligono_ha([[lon, lat] for lat, lon in vertices]) if len(vertices) >= MIN_PUNTOS else 0.0


def _se_cruzan(p1, p2, p3, p4) -> bool:
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = orient(p3, p4, p1), orient(p3, p4, p2), orient(p1, p2, p3), orient(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def contorno_cruzado(vertices: list) -> bool:
    """True si, al unir los puntos en el orden tocado, algún lado cruza a otro (figura en forma de «8»)."""
    n = len(vertices)
    if n < 4:
        return False
    lados = [(vertices[i], vertices[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):  # lados vecinos comparten un punto
                continue
            if _se_cruzan(*lados[i], *lados[j]):
                return True
    return False


def confirmar_contorno(ss) -> bool:
    """Une los puntos en el orden en que se tocaron, cierra el contorno y lo deja como terreno de la parcela."""
    v = ss.get("mp_vertices") if isinstance(ss, dict) else getattr(ss, "mp_vertices", [])
    if not v or len(v) < MIN_PUNTOS:
        return False
    pol = _poligono_de(v)
    punto = _centroide(pol)
    if isinstance(ss, dict):
        ss["reg_poligono"] = pol
        ss["reg_punto"] = punto
        ss["mp_cerrado"] = True
    else:
        ss.reg_poligono = pol
        ss.reg_punto = punto
        ss.mp_cerrado = True
    return True


def contorno_pendiente(ss) -> bool:
    """Hay puntos marcados (3 o más) que todavía no se confirmaron."""
    return ss.get("mp_modo") == "esquinas" and not ss.get("mp_cerrado") and len(ss.get("mp_vertices") or []) >= MIN_PUNTOS


def _icono_numero(i: int) -> folium.DivIcon:
    color = NARANJA if i == 0 else AMARILLO
    return folium.DivIcon(html=f"<div class='agro-vertice' style='background:{color}'>{i + 1}</div>",
                          icon_size=(24, 24), icon_anchor=(12, 12))


def _capas(ss) -> folium.FeatureGroup:
    """Lo que cambia en cada toque (puntos, líneas, contorno) se dibuja aparte, sin recargar el mapa base."""
    fg = folium.FeatureGroup(name=tr("Tu parcela"))
    v = ss.mp_vertices
    if ss.reg_poligono:
        ha = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
        folium.GeoJson(
            ss.reg_poligono,
            style_function=lambda _: {"color": AMARILLO, "weight": 3.5, "fillColor": VERDE_POL, "fillOpacity": 0.25},
            tooltip=tr(f"Tu terreno: {fmt(ha, 2)} ha (≈ {fmt(ha / 0.7, 1)} cuadras)"),
        ).add_to(fg)
    elif len(v) >= 2:
        # Recorrido en el orden en que se tocaron los puntos (aún sin cerrar)
        folium.PolyLine(v, color=AMARILLO, weight=3.5, opacity=0.95).add_to(fg)
        if len(v) >= MIN_PUNTOS:  # vista previa del lado que cerrará el contorno al confirmar
            folium.PolyLine([v[-1], v[0]], color="#ffffff", weight=2, dash_array="6 8", opacity=0.9).add_to(fg)
    for i, (la, lo) in enumerate(v):
        # interactive=False: un toque encima de un punto sigue llegando al mapa
        folium.Marker([la, lo], icon=_icono_numero(i), interactive=False).add_to(fg)
    folium.Marker(ss.reg_punto, tooltip=tr("Centro de tu parcela"),
                  icon=folium.Icon(color="green", icon="leaf", prefix="fa")).add_to(fg)
    return fg


def selector(editando=None, ndvi: bool = False):
    """Dibuja el selector y deja el resultado en st.session_state.reg_punto (lat, lon) y reg_poligono (GeoJSON)."""
    ss = st.session_state
    ss.setdefault("mp_vertices", [])
    ss.setdefault("mp_version", 0)
    ss.setdefault("mp_ultimo_clic", None)
    ss.setdefault("mp_ultimo_dibujo", None)
    ss.setdefault("mp_modo", "esquinas")
    ss.setdefault("mp_cerrado", bool(ss.get("reg_poligono")))
    if "mp_centro" not in ss or ss.get("mp_de") != ss.reg_de:
        ss.mp_de = ss.reg_de
        ss.mp_centro, ss.mp_zoom = list(ss.reg_punto), ss.reg_zoom
        ss.mp_vertices = _vertices_de(ss.get("reg_poligono"))
        ss.mp_cerrado = bool(ss.reg_poligono)
        ss.mp_version += 1

    theme.subtitulo_icono("pin", "1. ¿Dónde está tu terreno?")
    with st.expander("¿Cómo marcar mi terreno de forma fácil? (Guía rápida del mapa)", icon=":material/help:", expanded=False):
        st.markdown(
            "Hay dos formas muy fáciles de registrar tu terreno:\n\n"
            "- **Opción A (Recomendada) · Tocar las esquinas:** Toca cada esquina en el mapa satelital recorriendo el borde. "
            "Al marcar 3 o más esquinas verás el área en hectáreas. Para cerrar, toca el punto 1 (naranja), presiona «Confirmar contorno» "
            "o simplemente completa los datos abajo y guarda (se cerrará automáticamente).\n"
            "- **Opción B · Solo un punto:** Elige «Marcar solo un punto» arriba, toca el centro de tu terreno y escribe las hectáreas abajo.\n"
            "- **Herramientas de dibujo:** En la barra izquierda del mapa también tienes herramientas para dibujar polígonos o rectángulos arrastrando.\n"
            "- **Ubicar tu zona:** Usa el selector de cantones, el buscador de comunidades o el botón GPS (mi ubicación)."
        )

    m1, m2 = st.columns(2)
    for col, (clave, (titulo, desc, ic)) in zip((m1, m2), TARJETAS_MODO.items()):
        if col.button(f"**{tr(titulo)}**  \n{tr(desc)}", key=f"modo_{clave}", icon=ic, width="stretch",
                      type="primary" if ss.mp_modo == clave else "secondary"):
            if ss.mp_modo != clave:
                ss.mp_modo = clave
                if clave == "esquinas" and not ss.reg_poligono:
                    ss.mp_cerrado = False
                st.rerun()

    cantones = [c for c in CANTONES if c["altitud"] > 2000]
    u1, u2 = st.columns([1.4, 1], vertical_alignment="center")
    ir_a = u1.selectbox("Ir a un cantón", [None] + [c["id"] for c in cantones], label_visibility="collapsed",
                        format_func=lambda k: "Ir a un cantón…" if k is None else next(c["nombre"] for c in cantones if c["id"] == k),
                        key=f"ir_canton_{ss.mp_version}")
    if ir_a and ir_a != ss.get("mp_canton"):
        c = next(c for c in cantones if c["id"] == ir_a)
        ss.mp_canton = ir_a
        ss.mp_centro, ss.mp_zoom = [c["lat"], c["lon"]], 16
        ss.reg_punto = (c["lat"], c["lon"])
        ss.mp_version += 1
        st.rerun()
    if u2.button("Acercar a mi terreno", icon=":material/zoom_in:", width="stretch"):
        ss.mp_centro, ss.mp_zoom = list(ss.reg_punto), 19
        ss.mp_version += 1
        st.rerun()

    v = ss.mp_vertices
    if ss.mp_modo == "esquinas":
        b1, b2, b3 = st.columns(3)
        if b1.button("Deshacer último punto", icon=":material/undo:", disabled=not v or ss.mp_cerrado, width="stretch"):
            v.pop()
            st.rerun()
        if ss.mp_cerrado:
            if b2.button("Editar puntos", icon=":material/edit:", width="stretch",
                         help="Reabre el contorno para agregar o quitar puntos; luego vuelve a confirmarlo."):
                if not ss.mp_vertices and ss.reg_poligono:
                    ss.mp_vertices = _vertices_de(ss.reg_poligono)
                ss.reg_poligono, ss.mp_ultimo_dibujo = None, None
                ss.mp_cerrado = False
                ss.mp_version += 1
                st.rerun()
        else:
            txt_conf = f"Confirmar contorno ({len(v)} esquinas · {fmt(_area_vertices(v), 2)} ha)" if len(v) >= MIN_PUNTOS else "Confirmar contorno"
            if b2.button(txt_conf, icon=":material/check_circle:", type="primary" if len(v) >= MIN_PUNTOS else "secondary", width="stretch",
                         disabled=len(v) < MIN_PUNTOS, key="confirmar_contorno",
                         help="Une los puntos en el orden en que los tocaste y cierra el terreno."):
                if confirmar_contorno(ss):
                    st.toast(tr(f"Contorno confirmado: {fmt(_area_vertices(v), 2)} ha"), icon=":material/check_circle:")
                st.rerun()
        if b3.button("Borrar dibujo", icon=":material/delete:", disabled=not (v or ss.reg_poligono), width="stretch"):
            ss.mp_vertices, ss.reg_poligono, ss.mp_ultimo_dibujo = [], None, None
            ss.mp_cerrado = False
            ss.mp_version += 1
            st.rerun()

        if ss.reg_poligono and ss.mp_cerrado:
            ha_pol = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
            estado = (f"✅ Contorno confirmado · área aproximada **{fmt(ha_pol, 2)} ha** (≈ {fmt(ha_pol / 0.7, 1)} cuadras). "
                      "Si quieres ajustarlo, presiona **Editar puntos** o **Borrar dibujo**.")
        elif len(v) >= MIN_PUNTOS:
            ha_prev = _area_vertices(v)
            estado = (f"Llevas **{len(v)} esquinas** (≈ {fmt(ha_prev, 2)} ha). Toca otra esquina, toca el punto 1 (naranja) para cerrar, "
                      "o presiona **Confirmar contorno**.")
        elif len(v) == 2:
            estado = "Llevas **2 esquinas**. Toca la 3ª para comenzar a formar el área de tu terreno."
        elif len(v) == 1:
            estado = "Marcaste la **1ª esquina**. Toca la siguiente esquina recorriendo el borde de tu terreno."
        else:
            estado = "Toca las esquinas de tu terreno en el mapa satelital (en orden, recorriendo el borde)."
    else:
        estado = "Toca una vez en el mapa para marcar el punto de ubicación de tu terreno."
    st.info(estado, icon=":material/touch_app:")
    if ss.mp_modo == "esquinas" and contorno_cruzado(v):
        st.warning("Algunas líneas se cruzan: los puntos no siguen el borde del terreno. Usa **Deshacer último punto** "
                   "o **Borrar dibujo** y tócalos en orden (en el sentido del reloj o al revés).", icon=":material/warning:")

    # No devolver center/zoom ni reenviarlos en st_folium evita reiniciar el acercamiento al hacer clic
    idioma = "en" if en_ingles() else "es"
    out = st_folium(
        _mapa_base(list(ss.mp_centro), ss.mp_zoom, ndvi),
        key=f"mapa_registro_{ss.mp_version}_{idioma}",
        height=520,
        use_container_width=True,
        feature_group_to_add=_capas(ss),
        returned_objects=["last_clicked", "all_drawings", "last_active_drawing"],
    )
    if out:
        clic = out.get("last_clicked")
        dib_activo = out.get("last_active_drawing")
        dibujos = [d for d in (out.get("all_drawings") or []) if d.get("geometry", {}).get("type") == "Polygon"]
        cand = dib_activo if (dib_activo and dib_activo.get("geometry", {}).get("type") == "Polygon") else (dibujos[-1] if dibujos else None)
        if cand and cand != ss.mp_ultimo_dibujo:
            ss.mp_ultimo_dibujo = cand
            ss.reg_poligono = cand
            ss.reg_punto = _centroide(cand)
            ss.mp_vertices = _vertices_de(cand)
            ss.mp_cerrado = True
            ss.mp_modo = "esquinas"
            if clic:
                ss.mp_ultimo_clic = (round(clic["lat"], 7), round(clic["lng"], 7))
            st.rerun()
        elif ss.mp_ultimo_dibujo is not None and "all_drawings" in out and not dibujos:
            ss.mp_ultimo_dibujo = None
            ss.reg_poligono = None
            ss.mp_vertices = []
            ss.mp_cerrado = False
            st.rerun()
        elif clic:
            k = (round(clic["lat"], 7), round(clic["lng"], 7))
            if k != ss.mp_ultimo_clic:
                ss.mp_ultimo_clic = k
                if ss.mp_modo == "esquinas":
                    if not ss.mp_cerrado:
                        # Si ya hay 3 o más puntos y se toca cerca de la 1ra esquina (naranja), cerrar contorno
                        if len(ss.mp_vertices) >= MIN_PUNTOS:
                            p0 = ss.mp_vertices[0]
                            dist_m = distancia_km(clic["lat"], clic["lng"], p0[0], p0[1]) * 1000
                            if dist_m <= 35:
                                if confirmar_contorno(ss):
                                    ss.mp_version += 1
                                    st.toast(tr(f"Contorno cerrado: {fmt(_area_vertices(ss.mp_vertices), 2)} ha"), icon=":material/check_circle:")
                                st.rerun()
                        ss.mp_vertices.append([clic["lat"], clic["lng"]])
                        st.rerun()
                else:
                    ss.reg_punto = (clic["lat"], clic["lng"])
                    ss.reg_poligono = None
                    ss.mp_vertices = []
                    ss.mp_cerrado = False
                    st.rerun()

    ha_pol = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0]) if ss.reg_poligono else None
    ha_prev = _area_vertices(ss.mp_vertices) if len(ss.mp_vertices) >= MIN_PUNTOS else None
    area = ha_pol or ha_prev
    if area and area > 20:
        st.warning(f"El contorno mide {fmt(area, 1)} ha. Si tu terreno es más pequeño, presiona «Borrar dibujo», "
                   "acércate con «Acercar a mi terreno» y vuelve a tocar las esquinas.")
    if ha_pol:
        detalle = f" · Terreno confirmado: **{fmt(ha_pol, 2)} ha** (≈ {fmt(ha_pol / 0.7, 1)} cuadras)"
    elif ha_prev:
        detalle = f" · Contorno en progreso: **{fmt(ha_prev, 2)} ha** (toca la esquina 1 o «Confirmar»)"
    else:
        detalle = " · aún sin contorno (opcional)"
    st.caption(f"Punto: {ss.reg_punto[0]:.5f}, {ss.reg_punto[1]:.5f}" + detalle)
    return area
