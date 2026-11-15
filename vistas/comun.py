"""Elementos visuales compartidos por las vistas."""
import folium
import streamlit as st
from folium.plugins import Draw, Fullscreen, MeasureControl

from ui import theme
from utils.calculos import MESES_L


def fmt(n: float, dec: int = 0) -> str:
    """Número con formato ecuatoriano: 1.234,5"""
    s = f"{n:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def es_tecnica() -> bool:
    return st.session_state.get("modo") == "tecnica"


def ir(pagina: str, **kw):
    st.session_state.pagina = pagina
    for k, v in kw.items():
        st.session_state[k] = v
    st.rerun()


def estilos():
    """CSS global del sistema de diseño (ui/theme.py)."""
    theme.aplicar()


def encabezado(titulo: str, subtitulo: str = "", miga: str = "", icono_miga: str | None = None):
    theme.encabezado(titulo, subtitulo, miga, icono_miga)


def kpis(items: list[tuple]):
    theme.kpis(items)


def portada():
    theme.encabezado("AgroCycle", "¿Qué sembrar después de tu cosecha?", miga="Inicio", icono_miga="brote")
    st.write("Te ayudamos a planificar la **rotación de cultivos** de tu terreno con información del clima y del relieve "
             "de la **NASA**, las características de tu suelo, lo que sembraste antes y lo que más te importa.")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='tarjeta'>{theme.titulo_icono('⛰️', '1. Registra tu parcela')}Márcala en el mapa satelital y cuéntanos si tienes riego.</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='tarjeta'>{theme.titulo_icono('📜', '2. Cuenta qué sembraste')}Así evitamos repetir plagas y aprovechamos el abono que quedó.</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='tarjeta'>{theme.titulo_icono('🌿', '3. Recibe 3 opciones')}Con fechas, cosecha esperada y por qué conviene cada una.</div>", unsafe_allow_html=True)
    st.info("Para empezar, elige o registra un agricultor en la barra lateral.", icon=":material/arrow_back:")


ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services"
MAPA_CSS = """<style>
.leaflet-container{font-family:Inter,system-ui,sans-serif;background:#dfe5da}
.leaflet-bar a,.leaflet-control-layers-toggle{border-radius:8px!important}
.leaflet-bar{border:0!important;box-shadow:0 2px 10px rgba(0,0,0,.25)!important;border-radius:10px!important;overflow:hidden}
.leaflet-control-layers{border:0!important;border-radius:12px!important;box-shadow:0 2px 12px rgba(0,0,0,.25)!important;padding:4px 6px}
.leaflet-control-layers-expanded{font-size:13px;line-height:1.7}
.leaflet-popup-content-wrapper{border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.2)}
.leaflet-popup-content{margin:12px 14px;font-size:13px;line-height:1.45}
.leaflet-control-mouseposition{background:rgba(15,41,30,.85)!important;color:#fff!important;padding:3px 8px!important;
  border-radius:8px;font-size:11.5px;font-family:ui-monospace,Consolas,monospace}
.leaflet-control-attribution{font-size:10px!important;background:rgba(255,255,255,.75)!important;border-radius:6px 0 0 0}
.leaflet-control-scale-line{border-color:#fff!important;color:#fff!important;background:rgba(22,48,30,.6)!important;text-shadow:none}
.etiqueta-parcela{background:#fff;color:#14532D;border:1.5px solid #16A34A;border-radius:999px;padding:3px 10px;font-weight:700;
  font-size:12px;box-shadow:0 4px 12px rgba(15,41,30,.25);white-space:nowrap}
.etiqueta-parcela:before{display:none}
.leaflet-control-minimap{border-radius:10px!important;border:2px solid #fff!important;box-shadow:0 2px 10px rgba(0,0,0,.3)!important}
.leaflet-tile-pane{image-rendering:auto}
</style>"""


def capas_base(m: folium.Map, ndvi: bool = False):
    """Capas comunes: Google Satélite Híbrido activo por defecto y capas secundarias ocultas hasta seleccionarse."""
    from branca.element import Element
    folium.TileLayer(
        "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&hl=es",
        attr="Imágenes © Google · Maxar · CNES/Airbus",
        name="Satélite nítido (con nombres)",
        max_zoom=22,
        max_native_zoom=20,
        show=True,
    ).add_to(m)
    folium.TileLayer(
        "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Imágenes © Google · Maxar · CNES/Airbus",
        name="Satélite (solo terreno)",
        max_zoom=22,
        max_native_zoom=20,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        f"{ESRI}/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}",
        attr="Imágenes © Esri, Maxar, Earthstar Geographics",
        name="Satélite Esri",
        max_zoom=22,
        max_native_zoom=19,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap · © CARTO",
        name="Calles",
        max_zoom=22,
        max_native_zoom=19,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="© OpenTopoMap (CC-BY-SA)",
        name="Relieve",
        max_zoom=20,
        max_native_zoom=17,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        f"{ESRI}/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}",
        attr="Esri",
        name="Nombres de lugares",
        overlay=True,
        show=False,
        max_zoom=22,
        max_native_zoom=17,
    ).add_to(m)
    folium.TileLayer(
        f"{ESRI}/Reference/World_Transportation/MapServer/tile/{{z}}/{{y}}/{{x}}",
        attr="Esri",
        name="Vías",
        overlay=True,
        show=False,
        max_zoom=22,
        max_native_zoom=17,
        opacity=0.8,
    ).add_to(m)
    if ndvi:
        from datetime import date, timedelta
        f = (date.today() - timedelta(days=45)).isoformat()
        folium.TileLayer(f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/{f}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png",
                         attr="NASA GIBS · MODIS NDVI", name="Vegetación NDVI (NASA MODIS)", overlay=True, opacity=0.6,
                         max_native_zoom=9, max_zoom=22, show=False).add_to(m)
    m.get_root().header.add_child(Element(MAPA_CSS))


def controles(m: folium.Map, minimapa: bool = False, medir: bool = True):
    from folium.plugins import MiniMap, MousePosition
    Fullscreen(position="topleft", title="Pantalla completa", title_cancel="Salir de pantalla completa").add_to(m)
    if medir:
        MeasureControl(position="topleft", primary_length_unit="meters", secondary_length_unit=None,
                       primary_area_unit="hectares", secondary_area_unit="sqmeters").add_to(m)
    MousePosition(position="bottomleft", separator=" , ", prefix="Coord.", num_digits=5, empty_string="").add_to(m)
    if minimapa:
        MiniMap(tile_layer=folium.TileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
                                            attr="CARTO"), position="bottomright", width=130, height=110,
                zoom_level_offset=-6, toggle_display=True).add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)


def _area_txt(poligono: dict) -> str:
    from utils.calculos import area_poligono_ha
    try:
        return f"{fmt(area_poligono_ha(poligono['geometry']['coordinates'][0]), 2)} ha"
    except Exception:
        return ""


def mapa(lat: float, lon: float, zoom: int = 18, poligono: dict | None = None, dibujar: bool = True,
         ndvi: bool = False, marcador: bool = True, nombre: str = "Tu parcela", minimapa: bool = False) -> folium.Map:
    """Mapa de una parcela: híbrido satelital de alta resolución, contorno con su área y herramientas opcionales."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True, max_zoom=22)
    capas_base(m, ndvi)
    if poligono:
        g = folium.GeoJson(
            poligono,
            name="Contorno de la parcela",
            style_function=lambda _: {"color": "#facc15", "weight": 3.5, "fillColor": "#22c55e", "fillOpacity": 0.28},
            tooltip=folium.Tooltip(f"{nombre} · {_area_txt(poligono)}", sticky=True),
        )
        g.add_to(m)
        b = g.get_bounds()
        if max(b[1][0] - b[0][0], b[1][1] - b[0][1]) >= 0.0012:
            m.fit_bounds(b, padding=(45, 45), max_zoom=19)
        else:
            m.options["zoom"] = max(zoom, 18)
    if marcador:
        folium.Marker([lat, lon], tooltip=folium.Tooltip(nombre, permanent=True, direction="top", offset=(0, -34),
                                                         class_name="etiqueta-parcela"),
                      icon=folium.Icon(color="green", icon="leaf", prefix="fa")).add_to(m)
    if dibujar:
        shape = {"color": "#facc15", "weight": 3.5, "fillColor": "#22c55e", "fillOpacity": 0.25}
        Draw(export=False, position="topleft",
             draw_options={"polyline": False, "circle": False, "circlemarker": False, "marker": False,
                           "rectangle": {"showArea": True, "metric": ["ha", "m"], "shapeOptions": shape},
                           "polygon": {"allowIntersection": False, "showArea": True, "metric": ["ha", "m"], "shapeOptions": shape}},
             edit_options={"edit": True, "remove": True}).add_to(m)
    controles(m, minimapa=minimapa, medir=dibujar)
    return m


def mapa_general(lista: list, colores: dict | None = None, seleccion: int | None = None) -> folium.Map:
    """Todas las parcelas del agricultor en un mapa: contornos, badges blancos con borde verde y ficha al hacer clic."""
    import json
    from utils.validaciones import AGUA
    colores = colores or {}
    pts = [(p.latitud, p.longitud) for p in lista]
    centro = [sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)]
    m = folium.Map(location=centro, zoom_start=16, tiles=None, control_scale=True, max_zoom=22)
    capas_base(m)
    fg = folium.FeatureGroup(name="Parcelas").add_to(m)
    limites = []
    for p in lista:
        c = colores.get(p.id_parcela, "#2f6b3a")
        ficha = (f"<b style='font-size:14px'>{p.nombre}</b><br>{fmt(p.superficie, 2)} ha · {AGUA[p.disponibilidad_agua]}"
                 f"<br><span style='color:#64748B'>{p.latitud:.5f}, {p.longitud:.5f}</span>")
        if p.poligono:
            pol = json.loads(p.poligono)
            gj = folium.GeoJson(pol, style_function=lambda _, c=c: {"color": "#ffffff", "weight": 2.5, "fillColor": c, "fillOpacity": 0.45},
                                highlight_function=lambda _: {"weight": 4, "fillOpacity": 0.6},
                                tooltip=folium.Tooltip(p.nombre, permanent=True, class_name="etiqueta-parcela", direction="center"),
                                popup=folium.Popup(ficha, max_width=260))
            gj.add_to(fg)
            b = gj.get_bounds()
            limites += [b[0], b[1]]
        else:
            folium.CircleMarker([p.latitud, p.longitud], radius=11, color="#fff", weight=3, fill=True, fill_color=c, fill_opacity=1,
                                tooltip=folium.Tooltip(p.nombre, permanent=True, class_name="etiqueta-parcela", direction="top",
                                                       offset=(0, -12)),
                                popup=folium.Popup(ficha, max_width=260)).add_to(fg)
            limites.append([p.latitud, p.longitud])
    if limites:
        las, los = [x[0] for x in limites], [x[1] for x in limites]
        if max(las) - min(las) < 1e-4 and max(los) - min(los) < 1e-4:
            m.location, m.options["zoom"] = [las[0], los[0]], 18
        else:
            m.fit_bounds([[min(las), min(los)], [max(las), max(los)]], padding=(50, 50), max_zoom=18)
    controles(m, minimapa=False, medir=False)  # mapa de consulta: sin herramientas ni minimapa encima de los lotes
    return m


def meses_texto(meses: list[int], max_n: int = 3) -> str:
    if not meses:
        return ""
    return ", ".join(MESES_L[m] for m in meses) if len(meses) <= max_n else f"{', '.join(MESES_L[m] for m in meses[:max_n])} y otros"


def confianza_html(conf: dict) -> str:
    return f"<span class='conf {conf['nivel']}'>Confianza {conf['nivel'].lower()}</span>"
