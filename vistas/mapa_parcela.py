"""Selector de parcela en el mapa, pensado para que sea fácil marcar y dibujar el terreno.

Tres formas de hacerlo:
  1. Marcar el centro: un toque en el mapa.
  2. Dibujar tocando las esquinas: cada toque agrega una esquina; se ve el área al instante (no hace falta usar herramientas).
  3. Herramientas del mapa (contorno / rectángulo) en español, con área en hectáreas, edición y borrado.
Además: buscador de lugares, botón «mi ubicación» (GPS), pantalla completa y vista satelital con mucho acercamiento.
"""
import folium
import streamlit as st
from branca.element import Element, MacroElement
from folium.plugins import Draw, Fullscreen, Geocoder, LocateControl
from jinja2 import Template
from streamlit_folium import st_folium

from modules.datos_ambientales import CANTONES
from ui import theme
from utils.calculos import area_poligono_ha
from vistas.comun import capas_base, fmt

MODOS = {"esquinas": "Dibujar el contorno", "punto": "Marcar solo un punto"}
TARJETAS_MODO = {  # clave: (título, descripción, icono)
    "esquinas": ("Dibujar el contorno", "Toca cada esquina; con 3 o más se cierra solo", ":material/polyline:"),
    "punto": ("Marcar solo un punto", "Un toque en el mapa ubica el centro", ":material/location_on:"),
}
AMARILLO = "#facc15"
VERDE_POL = "#22c55e"


class DibujoEnEspanol(MacroElement):
    """Traduce Leaflet.draw al español y evita conflictos con clics sueltos mientras se usa la barra de dibujo."""
    _template = Template("""{% macro script(this, kwargs) %}
    if (typeof L !== 'undefined' && L.drawLocal) {
      var d = L.drawLocal;
      d.draw.toolbar.actions.title = 'Cancelar el dibujo'; d.draw.toolbar.actions.text = 'Cancelar';
      d.draw.toolbar.finish.title = 'Terminar el dibujo'; d.draw.toolbar.finish.text = 'Terminar';
      d.draw.toolbar.undo.title = 'Borrar la última esquina'; d.draw.toolbar.undo.text = 'Deshacer';
      d.draw.toolbar.buttons.polygon = 'Dibujar el contorno de tu terreno';
      d.draw.toolbar.buttons.rectangle = 'Dibujar un terreno rectangular';
      d.draw.handlers.polygon.tooltip.start = 'Toca la primera esquina de tu terreno';
      d.draw.handlers.polygon.tooltip.cont = 'Toca la siguiente esquina';
      d.draw.handlers.polygon.tooltip.end = 'Toca la primera esquina para cerrar, o «Terminar»';
      d.draw.handlers.rectangle.tooltip.start = 'Presiona y arrastra para dibujar el rectángulo';
      d.draw.handlers.simpleshape.tooltip.end = 'Suelta para terminar';
      d.edit.toolbar.actions.save.title = 'Guardar los cambios'; d.edit.toolbar.actions.save.text = 'Guardar';
      d.edit.toolbar.actions.cancel.title = 'Cancelar'; d.edit.toolbar.actions.cancel.text = 'Cancelar';
      d.edit.toolbar.actions.clearAll.title = 'Borrar todo'; d.edit.toolbar.actions.clearAll.text = 'Borrar todo';
      d.edit.toolbar.buttons.edit = 'Mover las esquinas del dibujo'; d.edit.toolbar.buttons.editDisabled = 'No hay nada que editar';
      d.edit.toolbar.buttons.remove = 'Borrar el dibujo'; d.edit.toolbar.buttons.removeDisabled = 'No hay nada que borrar';
      d.edit.handlers.edit.tooltip.text = 'Arrastra las esquinas para ajustar el contorno';
      d.edit.handlers.edit.tooltip.subtext = 'Luego toca «Guardar»';
      d.edit.handlers.remove.tooltip.text = 'Toca el dibujo que quieres borrar';
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


CSS = """<style>
.leaflet-draw.leaflet-control{transform:scale(1.3);transform-origin:top left;margin-top:14px!important}
.leaflet-draw-actions a{font-size:13px!important;font-weight:600}
.leaflet-control-locate a,.leaflet-control-fullscreen a{width:38px!important;height:38px!important;line-height:38px!important}
.leaflet-draw-tooltip{font-size:13px!important}
.leaflet-control-geocoder{font-size:14px;border-radius:10px!important;border:0!important;box-shadow:0 2px 10px rgba(0,0,0,.25)!important}
.leaflet-control-geocoder-form input{width:230px;padding:6px 8px}
</style>"""


def _mapa_base(centro, zoom, ndvi: bool) -> folium.Map:
    """Mapa fijo (no cambia entre clics de esquinas) para mantener fluido el acercamiento del usuario."""
    m = folium.Map(location=centro, zoom_start=zoom, tiles=None, control_scale=True, max_zoom=22)
    capas_base(m, ndvi)
    m.get_root().header.add_child(Element(CSS))
    Geocoder(collapsed=False, position="topright", add_marker=False, zoom=18,
             placeholder="Buscar comunidad o lugar…", error_message="No se encontró ese lugar").add_to(m)
    LocateControl(position="topleft", flyTo=True, initialZoomLevel=19, strings={"title": "Ir a mi ubicación (GPS)"}).add_to(m)
    Fullscreen(position="topleft", title="Pantalla completa", title_cancel="Salir de pantalla completa").add_to(m)
    m.add_child(DibujoEnEspanol())
    forma = {"color": AMARILLO, "weight": 3.5, "fillColor": VERDE_POL, "fillOpacity": 0.25}
    Draw(position="topleft", show_geometry_on_click=False,
         draw_options={"polyline": False, "circle": False, "circlemarker": False, "marker": False,
                       "polygon": {"allowIntersection": False, "showArea": True, "metric": ["ha", "m"], "shapeOptions": forma},
                       "rectangle": {"showArea": True, "metric": ["ha", "m"], "shapeOptions": forma}},
         edit_options={"edit": True, "remove": True}).add_to(m)
    from folium.plugins import MousePosition
    MousePosition(position="bottomleft", separator=" , ", prefix="Coord.", num_digits=5, empty_string="").add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    return m


def _poligono_de(vertices: list) -> dict:
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


def _sincronizar_vertices(ss):
    """Mantiene cerrado automáticamente el polígono al tener 3 o más esquinas."""
    v = ss.mp_vertices
    if len(v) >= 3:
        ss.reg_poligono = _poligono_de(v)
        ss.reg_punto = _centroide(ss.reg_poligono)
    else:
        ss.reg_poligono = None


def _capas(ss) -> folium.FeatureGroup:
    """Lo que cambia en cada toque (marcador, contorno, esquinas) se dibuja aparte, sin recargar el mapa base."""
    fg = folium.FeatureGroup(name="Tu parcela")
    if ss.reg_poligono:
        ha = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
        folium.GeoJson(
            ss.reg_poligono,
            style_function=lambda _: {"color": AMARILLO, "weight": 3.5, "fillColor": VERDE_POL, "fillOpacity": 0.25},
            tooltip=f"Tu terreno: {fmt(ha, 2)} ha (≈ {fmt(ha / 0.7, 1)} cuadras)",
        ).add_to(fg)
    v = ss.mp_vertices
    if len(v) == 2:
        folium.PolyLine(v, color=AMARILLO, weight=3, dash_array="6 6").add_to(fg)
    for i, (la, lo) in enumerate(v):
        folium.CircleMarker(
            [la, lo],
            radius=9 if i == 0 else 7,
            color="#fff",
            weight=2.5,
            fill=True,
            fill_color="#f97316" if i == 0 else AMARILLO,
            fill_opacity=1,
            tooltip=f"Esquina {i + 1}",
        ).add_to(fg)
    folium.Marker(ss.reg_punto, tooltip="Centro de tu parcela", icon=folium.Icon(color="green", icon="leaf", prefix="fa")).add_to(fg)
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
    with st.expander("¿Cómo marco mi terreno? (rápido y sencillo)", icon=":material/help:", expanded=False):
        st.markdown(
            "1. **Ubica tu zona**: elige tu cantón, usa el buscador del mapa o toca el botón GPS.\n"
            "2. **Acércate** con la rueda del ratón o **Acercar a mi terreno** hasta ver con claridad los linderos.\n"
            "3. Toca cada esquina del terreno en el mapa: **desde la 3ra esquina el contorno se cierra solo** y calcula las hectáreas al instante.\n"
            "4. También puedes usar las herramientas de polígono o rectángulo en la esquina izquierda del mapa."
        )

    m1, m2 = st.columns(2)
    for col, (clave, (titulo, desc, ic)) in zip((m1, m2), TARJETAS_MODO.items()):
        if col.button(f"**{titulo}**  \n{desc}", key=f"modo_{clave}", icon=ic, width="stretch",
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
    b1, b2, b3 = st.columns(3)
    if b1.button("Deshacer esquina", icon=":material/undo:", disabled=not v, width="stretch"):
        v.pop()
        _sincronizar_vertices(ss)
        ss.mp_cerrado = False
        st.rerun()
    etiqueta_fin = "Reanudar esquinas" if ss.mp_cerrado else "Terminar contorno"
    icono_fin = ":material/edit:" if ss.mp_cerrado else ":material/check_circle:"
    if b2.button(etiqueta_fin, icon=icono_fin, type="primary" if (not ss.mp_cerrado and ss.reg_poligono) else "secondary",
                 disabled=not (ss.reg_poligono or ss.mp_cerrado), width="stretch"):
        ss.mp_cerrado = not ss.mp_cerrado
        if not ss.mp_cerrado and not ss.mp_vertices and ss.reg_poligono:
            ss.mp_vertices = _vertices_de(ss.reg_poligono)
        st.rerun()
    if b3.button("Borrar dibujo", icon=":material/delete:", disabled=not (v or ss.reg_poligono), width="stretch"):
        ss.mp_vertices, ss.reg_poligono, ss.mp_ultimo_dibujo = [], None, None
        ss.mp_cerrado = False
        ss.mp_version += 1
        st.rerun()

    if ss.mp_modo == "esquinas":
        if ss.reg_poligono and ss.mp_cerrado:
            ha_pol = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
            estado = (f"Contorno listo · área aproximada **{fmt(ha_pol, 2)} ha** (≈ {fmt(ha_pol / 0.7, 1)} cuadras). "
                      "Si quieres ajustarlo, toca **Reanudar esquinas** o **Borrar dibujo**.")
        elif ss.reg_poligono:
            ha_pol = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0])
            estado = (f"**{len(v)} esquinas** · contorno cerrado en **{fmt(ha_pol, 2)} ha** (≈ {fmt(ha_pol / 0.7, 1)} cuadras). "
                      "Toca otra esquina si deseas ampliarlo o presiona **Terminar contorno**.")
        elif v:
            estado = f"Llevas **{len(v)} esquina(s)**. Toca la siguiente en el mapa (desde la 3ra se cierra solo)."
        else:
            estado = "Toca las esquinas de tu terreno directamente en el mapa satelital (con 3 o más se forma el contorno)."
    else:
        estado = "Toca una vez en el mapa para marcar el punto de ubicación de tu terreno."
    st.info(estado, icon=":material/touch_app:")

    # No devolver center/zoom ni reenviarlos en st_folium evita reiniciar el acercamiento al hacer clic
    out = st_folium(
        _mapa_base(list(ss.mp_centro), ss.mp_zoom, ndvi),
        key=f"mapa_registro_{ss.mp_version}",
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
            ss.mp_vertices = []
            ss.mp_cerrado = True
            if clic:
                ss.mp_ultimo_clic = (round(clic["lat"], 7), round(clic["lng"], 7))
            st.rerun()
        elif ss.mp_ultimo_dibujo is not None and "all_drawings" in out and not dibujos and not ss.mp_vertices:
            ss.mp_ultimo_dibujo = None
            ss.reg_poligono = None
            ss.mp_cerrado = False
            st.rerun()
        elif clic:
            k = (round(clic["lat"], 7), round(clic["lng"], 7))
            if k != ss.mp_ultimo_clic:
                ss.mp_ultimo_clic = k
                if ss.mp_modo == "esquinas":
                    if not ss.mp_cerrado:
                        ss.mp_vertices.append([clic["lat"], clic["lng"]])
                        _sincronizar_vertices(ss)
                        st.rerun()
                else:
                    ss.reg_punto = (clic["lat"], clic["lng"])
                    ss.reg_poligono = None
                    ss.mp_vertices = []
                    ss.mp_cerrado = False
                    st.rerun()

    area = area_poligono_ha(ss.reg_poligono["geometry"]["coordinates"][0]) if ss.reg_poligono else None
    if area and area > 20:
        st.warning(f"El contorno mide {fmt(area, 1)} ha. Si tu terreno es más pequeño, presiona «Borrar dibujo», "
                   "acércate con «Acercar a mi terreno» y vuelve a tocar las esquinas.")
    st.caption(f"Punto: {ss.reg_punto[0]:.5f}, {ss.reg_punto[1]:.5f}" +
               (f" · Terreno dibujado: **{fmt(area, 2)} ha** (≈ {fmt(area / 0.7, 1)} cuadras)" if area else " · aún sin contorno (opcional)"))
    return area
