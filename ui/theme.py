"""Sistema de diseño de AgroCycle: CSS global, iconos SVG (Lucide, licencia ISC) y componentes reutilizables.

Los colores base, fuentes y bordes de los widgets nativos se definen en .streamlit/config.toml;
aquí va lo que el tema nativo no cubre (tarjetas, KPI, insignias, pasos, avatares, mapas y fusión).
"""
from html import escape

import streamlit as st

_RELOAD_TAG = "agrocycle_v4_satelite_2026"

# ------------------------------------------------------------------ paleta
BOSQUE = "#0F291E"      # barra lateral
ESMERALDA = "#10B981"   # acento activo
VERDE = "#16A34A"       # acción principal / foco
VERDE_OSC = "#15803D"
AMBAR = "#D97706"
PIZARRA = "#64748B"
TINTA = "#1E293B"
BORDE = "#E2E8F0"
FONDO = "#F6F8F7"

# ------------------------------------------------------------------ iconos (trazos Lucide, 24x24)
_ICONOS = {
    "mapa": '<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" x2="9" y1="3" y2="18"/><line x1="15" x2="15" y1="6" y2="21"/>',
    "capas": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "calendario": '<rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/>'
                  '<line x1="3" x2="21" y1="10" y2="10"/><path d="m9 16 2 2 4-4"/>',
    "gota": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "usuarios": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
                '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "hoja": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>'
            '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "lapiz": '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "alerta": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/>'
              '<line x1="12" x2="12.01" y1="17" y2="17"/>',
    "satelite": '<path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/>',
    "lluvia": '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/>',
    "termometro": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "montana": '<path d="m8 3 4 8 5-5 5 15H2L8 3z"/>',
    "historial": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    "brote": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/>'
             '<path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "escudo": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "tendencia": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "ojo": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/>'
           '<circle cx="12" cy="12" r="3"/>',
    "herramienta": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    "enviar": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "grafico": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "radar": '<path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h.01"/><path d="M2.29 9.62A10 10 0 1 0 21.31 8.35"/>'
             '<path d="M16.24 7.76A6 6 0 1 0 8.23 16.67"/><path d="M12 18h.01"/><path d="M17.99 11.66A6 6 0 0 1 15.77 16.67"/>'
             '<circle cx="12" cy="12" r="2"/><path d="m13.41 10.59 5.66-5.66"/>',
}


def icono(nombre: str, tam: int = 18, color: str = "currentColor", grosor: float = 2) -> str:
    """SVG en línea de la colección Lucide."""
    trazo = _ICONOS.get(nombre, _ICONOS["hoja"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazo}</svg>')


# ------------------------------------------------------------------ CSS global
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

/* ===== Ocultar por completo el cromo por defecto de Streamlit ===== */
#MainMenu, header, header[data-testid="stHeader"], footer,
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"], .stDeployButton, [data-testid="stSidebarCollapseButton"] {
  display:none!important;
  visibility:hidden!important;
  height:0!important;
}
html, body, [data-testid="stAppViewContainer"] {
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  background-color:#F6F8F7;
  color:#1E293B;
}
.block-container{padding-top:1.5rem;padding-bottom:3rem;max-width:1260px}
h1,h2,h3,h4{font-family:'Plus Jakarta Sans','Inter',sans-serif;letter-spacing:-.02em}

/* ===== Barra lateral verde bosque profundo ===== */
section[data-testid="stSidebar"]{
  background-color:#0F291E;
  border-right:1px solid rgba(255,255,255,.08);
  min-width:310px!important;
  max-width:330px!important;
}
.block-container,
[data-testid="stMainBlockContainer"] {
  max-width: 100% !important;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
}
section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.08);margin:.55rem 0}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#9DB5A8!important}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background:#173A2B;
  border:1px solid #2A4A3C;
  border-radius:10px;
  min-height:40px;
  padding-top:4px;
  padding-bottom:4px;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] div {
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:unset!important;
  line-height:1.3!important;
  font-size:.86rem!important;
  color:#F3F6F4!important;
}
.marca{display:flex;align-items:center;gap:11px;padding:.15rem 0 .65rem}
.marca .logo{width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,#34D399,#047857);display:flex;
  align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(16,185,129,.35);flex-shrink:0}
.marca b{font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:1.12rem;color:#fff;letter-spacing:-.01em}
.marca small{display:block;color:#9DB5A8;font-size:.72rem;margin-top:1px;white-space:nowrap}
.seccion{font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#7FA08F;margin:.6rem 0 .28rem}
.persona{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);
  border-radius:12px;padding:9px 11px;margin:.25rem 0 .35rem}
.persona .av{width:34px;height:34px;font-size:.76rem}
.persona b{display:block;color:#F3F6F4;font-size:.87rem;line-height:1.25;white-space:normal;word-break:break-word}
.persona small{display:block;color:#9DB5A8;font-size:.74rem;line-height:1.32;white-space:normal;word-break:break-word;margin-top:1px}
/* Control segmentado / pill toggle moderno */
section[data-testid="stSidebar"] [data-testid="stButtonGroup"]{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
  border-radius:999px;padding:3px;width:100%}
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] [role="radiogroup"]{width:100%;gap:3px;display:flex}
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] button{flex:1;border:0!important;border-radius:999px!important;
  background:transparent!important;color:#C4D7CD!important;font-weight:600;font-size:.86rem;transition:all .18s ease;min-height:34px}
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-checked="true"]{background:#10B981!important;
  color:#05261A!important;box-shadow:0 2px 10px rgba(16,185,129,.38)}
/* Menú de navegación */
section[data-testid="stSidebar"] .st-key-menu [data-testid="stButton"]{margin-bottom:-.55rem}
section[data-testid="stSidebar"] .st-key-menu button{justify-content:flex-start;background:transparent;border:0;color:#C9D8CF;
  font-weight:500;padding:.5rem .75rem;min-height:0;border-radius:10px;transition:background .15s ease}
section[data-testid="stSidebar"] .st-key-menu button>div,section[data-testid="stSidebar"] .st-key-menu button>div>span{justify-content:flex-start!important;width:100%}
section[data-testid="stSidebar"] .st-key-menu button:hover{background:rgba(255,255,255,.06);color:#fff}
section[data-testid="stSidebar"] .st-key-menu button[kind="primary"]{background:rgba(16,185,129,.16);color:#fff;font-weight:650;
  box-shadow:inset 3px 0 0 #10B981}
section[data-testid="stSidebar"] .st-key-menu button[kind="primary"] [data-testid="stIconMaterial"]{color:#34D399}

/* ===== Encabezado de página ===== */
.encabezado{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:0 0 1.2rem;padding-bottom:1rem;
  border-bottom:1px solid #E2E8F0}
.encabezado .miga{display:inline-flex;align-items:center;gap:6px;font-size:.74rem;font-weight:700;color:#15803D;text-transform:uppercase;
  letter-spacing:.08em}
.encabezado h1{font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:2rem;font-weight:800;margin:.25rem 0 .2rem;padding:0;
  line-height:1.15;color:#0F172A}
.encabezado p{margin:0;color:#64748B;font-size:.95rem}
.subtitulo-ico{display:flex;align-items:center;gap:9px;font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:1.12rem;
  font-weight:700;color:#0F172A;margin:.85rem 0 .55rem}
.subtitulo-ico .circ{width:30px;height:30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}

/* ===== Tarjetas ===== */
.tarjeta,.kpi,.parcela,.panel,.bloque-info,.testigo-card{
  background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;box-shadow:0 4px 20px -2px rgba(15,41,30,.05)
}
.tarjeta{padding:16px 18px;margin-bottom:12px}
.tarjeta h3,.tarjeta h4{margin:0 0 .35rem}
.tarjeta.verde{background:linear-gradient(135deg,#0F291E,#166534);color:#fff;border:0}
.tarjeta.verde h3{color:#fff;margin:0 0 .3rem}
.testigo-card{padding:15px 18px;margin:10px 0 14px;border-left:4px solid #D97706;background:linear-gradient(90deg,#FFFBEB 0%,#FFFFFF 35%)}
.testigo-card.ok{border-left-color:#16A34A;background:linear-gradient(90deg,#F0FDF4 0%,#FFFFFF 35%)}
.bloque-info{padding:15px 18px;margin-bottom:12px;height:100%}
.bloque-info h4{display:flex;align-items:center;gap:8px;font-size:1rem;margin:0 0 .55rem;color:#0F172A}
.bloque-info ul{margin:0;padding-left:1.1rem;color:#334155;font-size:.92rem;line-height:1.5}
.bloque-info li{margin-bottom:.35rem}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]){border-radius:14px}
.st-key-panel,.st-key-panel_form{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:18px 20px;
  box-shadow:0 4px 20px -2px rgba(15,41,30,.05)}

/* ===== KPI ===== */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:0 0 18px}
.kpi{padding:16px 18px;position:relative}
.kpi .ico{position:absolute;top:14px;right:14px;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.kpi small{display:block;font-size:.74rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.05em;padding-right:44px}
.kpi b{display:block;font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:1.78rem;font-weight:800;color:#0F172A;margin:6px 0 6px;
  line-height:1.08;font-variant-numeric:tabular-nums}
.kpi .sub{font-size:.8rem;color:#64748B}

/* ===== Insignias, chips y avatares ===== */
.insignia{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:.74rem;font-weight:700;white-space:nowrap;
  border:1px solid transparent}
.insignia.ok{background:#DCFCE7;color:#166534;border-color:#BBF7D0}
.insignia.lista{background:#ECFDF5;color:#047857;border-color:#A7F3D0}
.insignia.falta{background:#FFFBEB;color:#B45309;border-color:#FDE68A}
.insignia.gris{background:#F1F5F9;color:#475569;border-color:#E2E8F0}
.chip{display:inline-block;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:999px;padding:3px 10px;margin:2px;font-weight:600;font-size:.85rem;color:#166534}
.tarjeta.verde .chip{background:#ffffff26;border-color:#ffffff40;color:#fff}
.av{width:38px;height:38px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;
  color:#fff;flex-shrink:0;font-family:'Plus Jakarta Sans',Inter,sans-serif}

/* ===== Tarjetas de parcela ===== */
.parcela{padding:16px 18px 12px;margin-bottom:8px;border-left:4px solid var(--c,#16A34A)}
.parcela .cab{display:flex;justify-content:space-between;align-items:center;gap:10px}
.parcela h3{font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:1.15rem;font-weight:700;margin:0;padding:0;color:#0F172A}
.parcela .datos{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0 10px}
.parcela .datos div{background:#F8FAFC;border:1px solid #F1F5F9;border-radius:10px;padding:8px 10px}
.parcela .datos small{display:flex;white-space:nowrap;align-items:center;gap:5px;font-size:.68rem;color:#64748B;text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.parcela .datos b{font-size:.9rem;line-height:1.3;color:#0F172A;font-variant-numeric:tabular-nums}
.parcela .pie{font-size:.84rem;color:#475569;border-top:1px dashed #E2E8F0;padding-top:8px}
.parcela.falta{background:linear-gradient(0deg,#FFFDF7,#FFFFFF)}

/* ===== Tabla de cartera ===== */
.tabla-cab{font-size:.72rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:.06em}
.st-key-cartera_cab [data-testid="stHorizontalBlock"]{padding:0 13px;margin-bottom:-14px}
.fila-nombre{display:flex;align-items:center;gap:11px;min-width:0}
.fila-nombre > div{min-width:0}
.fila-nombre b{display:block;color:#0F172A;font-size:.95rem}
.fila-nombre small{display:block;line-height:1.35;color:#64748B;font-size:.78rem;overflow-wrap:anywhere;word-break:break-word}
[data-testid="stMetricValue"] > div{overflow:visible!important;text-overflow:unset!important;white-space:normal!important}
.celda{font-size:.9rem;color:#334155;font-variant-numeric:tabular-nums}
.st-key-cartera [data-testid="stHorizontalBlock"]{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;margin-bottom:-6px;
  align-items:center}
.st-key-cartera [data-testid="stHorizontalBlock"]:hover{border-color:#86EFAC;box-shadow:0 4px 16px -4px rgba(15,41,30,.10)}

/* ===== Pasos del registro ===== */
.pasos{display:flex;flex-wrap:wrap;align-items:center;gap:8px 6px;background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:11px 16px;margin:0 0 16px;
  box-shadow:0 4px 20px -2px rgba(15,41,30,.05)}
.paso{display:flex;align-items:center;gap:9px;flex:0 0 auto}
.paso .n{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.82rem;
  background:#F1F5F9;color:#64748B;border:2px solid #E2E8F0;flex-shrink:0}
.paso b{font-size:.86rem;color:#64748B;font-weight:600;white-space:nowrap}
.paso.activo .n{background:#16A34A;color:#fff;border-color:#BBF7D0;box-shadow:0 0 0 4px #DCFCE7}
.paso.activo b{color:#0F172A;font-weight:700}
.paso.hecho .n{background:#DCFCE7;color:#15803D;border-color:#86EFAC}
.paso.hecho b{color:#15803D}
.raya{flex:1 1 14px;min-width:12px;height:2px;background:#E2E8F0;margin:0 8px;border-radius:2px}
.raya.hecha{background:#86EFAC}
/* Tarjetas seleccionables (modo de marcado) */
.st-key-modo_punto button,.st-key-modo_esquinas button{min-height:74px;justify-content:flex-start;text-align:left;padding:12px 15px;
  background:#fff;border:1.5px solid #E2E8F0;border-radius:14px;color:#334155;box-shadow:0 4px 20px -2px rgba(15,41,30,.05);transition:all .15s}
.st-key-modo_punto button:hover,.st-key-modo_esquinas button:hover{border-color:#86EFAC}
.st-key-modo_punto button p,.st-key-modo_esquinas button p{text-align:left;line-height:1.35;white-space:normal;overflow-wrap:break-word}
.st-key-modo_punto button[kind="primary"],.st-key-modo_esquinas button[kind="primary"]{background:#F0FDF4;border-color:#16A34A;color:#14532D;
  box-shadow:0 0 0 3px #DCFCE7}
.st-key-modo_punto button>div,.st-key-modo_esquinas button>div{justify-content:flex-start!important;width:100%}

/* ===== Botones, pestañas, expansores, formularios e inputs ===== */
.stButton button,.stDownloadButton button,.stFormSubmitButton button{font-weight:600;transition:all .15s ease}
.stButton button[kind="primary"],.stFormSubmitButton button[kind="primary"]{box-shadow:0 2px 8px -2px rgba(22,163,74,.45)}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid #E2E8F0}
.stTabs [data-baseweb="tab"]{font-weight:600;padding:8px 14px}
[data-testid="stExpander"] details{border-radius:12px;background:#fff;border:1px solid #E2E8F0}
[data-testid="stForm"]{background:#fff;border:1px solid #E2E8F0!important;border-radius:14px;padding:20px 22px;
  box-shadow:0 4px 20px -2px rgba(15,41,30,.05)}

/* Inputs en área principal: fondo blanco, borde #CBD5E1 y foco verde #16A34A */
[data-testid="stMain"] [data-testid="stTextInputRootElement"],
[data-testid="stMain"] [data-testid="stNumberInputContainer"],
[data-testid="stMain"] [data-testid="stTextAreaRootElement"],
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  background-color:#FFFFFF!important;
  border-color:#CBD5E1!important;
  border-radius:10px!important;
}
[data-testid="stTextInputRootElement"]:focus-within,[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stMain"] [data-baseweb="select"] > div:focus-within,
.react-aria-ComboBox [role="group"]:focus-within{
  border-color:#16A34A!important;
  box-shadow:0 0 0 3px rgba(22,163,74,.15)!important;
}

/* ===== Mapas ===== */
iframe[title="streamlit_folium.st_folium"]{border-radius:14px;border:1px solid #E2E8F0;box-shadow:0 4px 20px -2px rgba(15,41,30,.08)}
.leyenda{display:flex;flex-wrap:wrap;gap:16px;font-size:.82rem;color:#475569;margin:8px 2px 0}
.leyenda i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:0}

/* ===== Piezas de plan ===== */
.ciclo{border-left:7px solid var(--c);background:#fff;border-radius:14px;padding:14px 16px;margin-bottom:10px;border-top:1px solid #E2E8F0;
  border-right:1px solid #E2E8F0;border-bottom:1px solid #E2E8F0;box-shadow:0 2px 12px -2px rgba(15,41,30,.04)}
.ciclo h4{margin:0 0 4px;font-size:1.15rem}
.cifra{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:6px 10px;display:inline-block;margin:4px 6px 4px 0;font-variant-numeric:tabular-nums}
.cifra small{display:block;color:#64748B;font-size:.73rem;text-transform:uppercase;letter-spacing:.03em}
.alerta{color:#B45309}
.conf{display:inline-block;padding:3px 12px;border-radius:999px;font-weight:700;font-size:.85rem}
.conf.Alta{background:#DCFCE7;color:#166534}.conf.Media{background:#FEF3C7;color:#92400E}.conf.Baja{background:#FEE2E2;color:#B91C1C}
.luces{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.luz{background:#ffffff1f;border-radius:12px;padding:7px 12px;display:flex;flex-direction:column;min-width:135px}
.luz span{font-size:1.15rem}.luz small{opacity:.9}
.et{font-size:.75rem;font-weight:700;color:#15803D;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px}
.tarjeta.etapa{background:#F0FDF4;border-color:#DCFCE7;padding:10px 14px;min-height:96px}
</style>"""


def aplicar():
    """Inyecta el CSS global (una vez por ejecución)."""
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ componentes
def marca():
    st.markdown(f"<div class='marca'><div class='logo'>{icono('brote', 22, '#fff', 2.2)}</div><div><b>AgroCycle</b>"
                "<small>Rotación de cultivos · Chimborazo</small></div></div>", unsafe_allow_html=True)


def seccion(texto: str):
    st.markdown(f"<div class='seccion'>{escape(texto)}</div>", unsafe_allow_html=True)


ICONO_EMOJI = {
    "🌧️": ("lluvia", "#0284C7"),
    "🌡️": ("termometro", "#DC2626"),
    "💧": ("gota", "#0284C7"),
    "⛰️": ("montana", "#475569"),
    "🌿": ("hoja", "#16A34A"),
    "🟫": ("capas", "#92400E"),
    "📜": ("historial", "#7C3AED"),
}


def titulo_icono(emoji: str, titulo: str) -> str:
    """Título de tarjeta con icono SVG en círculo (traduce los iconos emoji que entregan los módulos)."""
    nombre, color = ICONO_EMOJI.get(emoji, ("hoja", VERDE))
    return (f"<h4 style='display:flex;align-items:center;gap:10px'><span style='width:34px;height:34px;border-radius:50%;"
            f"background:{color}1A;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0'>{icono(nombre, 18, color)}</span>"
            f"{escape(titulo)}</h4>")


def subtitulo_icono(nombre_icono: str, texto: str, color: str = VERDE_OSC):
    """Encabezado de sección limpio con icono vectorial SVG en círculo."""
    st.markdown(
        f"<div class='subtitulo-ico'><span class='circ' style='background:{color}18'>"
        f"{icono(nombre_icono, 17, color, 2.2)}</span><span>{escape(texto)}</span></div>",
        unsafe_allow_html=True,
    )


def iniciales(nombre: str) -> str:
    partes = [p for p in (nombre or "?").replace(".", " ").split() if p[:1].isalpha() and p.lower() not in ("de", "del", "la", "ing", "tec", "dr", "lic")]
    return ((partes[0][0] + (partes[1][0] if len(partes) > 1 else "")) if partes else "?").upper()


_COLORES_AV = ["#0E7490", "#7C3AED", "#B45309", "#15803D", "#BE185D", "#1D4ED8", "#0F766E", "#9333EA"]


def avatar(nombre: str, clase: str = "") -> str:
    color = _COLORES_AV[sum(map(ord, nombre or "")) % len(_COLORES_AV)]
    return f"<span class='av {clase}' style='background:{color}'>{escape(iniciales(nombre))}</span>"


def persona(nombre: str, detalle: str = ""):
    """Tarjeta compacta en dos líneas para la barra lateral (evita que los nombres largos se corten)."""
    st.markdown(f"<div class='persona'>{avatar(nombre)}<div><b>{escape(nombre)}</b>"
                f"{f'<small>{escape(detalle)}</small>' if detalle else ''}</div></div>", unsafe_allow_html=True)


def encabezado(titulo: str, subtitulo: str = "", miga: str = "", icono_miga: str | None = None):
    ic = icono(icono_miga, 14, VERDE_OSC, 2.4) if icono_miga else ""
    st.markdown(f"<div class='encabezado'><div>{f'<div class=miga>{ic}{escape(miga)}</div>' if miga else ''}<h1>{escape(titulo)}</h1>"
                f"{f'<p>{escape(subtitulo)}</p>' if subtitulo else ''}</div></div>", unsafe_allow_html=True)


def kpis(items: list[tuple]):
    """Fila de indicadores: [(etiqueta, valor, nota, icono, color), ...] (icono y color son opcionales)."""
    html = []
    for it in items:
        e, v, n = it[:3]
        ic, col = (it[3] if len(it) > 3 else "capas"), (it[4] if len(it) > 4 else VERDE)
        html.append(f"<div class='kpi'><div class='ico' style='background:{col}1A'>{icono(ic, 19, col, 2.1)}</div>"
                    f"<small>{escape(str(e))}</small><b>{escape(str(v))}</b><span class='sub'>{escape(str(n))}</span></div>")
    st.markdown("<div class='kpis'>" + "".join(html) + "</div>", unsafe_allow_html=True)


def insignia(texto: str, tipo: str = "gris", con_icono: bool = True) -> str:
    ic = {"ok": "check", "lista": "calendario", "falta": "alerta"}.get(tipo) if con_icono else None
    return f"<span class='insignia {tipo}'>{icono(ic, 12, 'currentColor', 2.6) if ic else ''}{escape(texto)}</span>"


def pasos(actual: int, nombres=("1. Ubicar terreno", "2. Datos de suelo y agua", "3. Generar plan anual")):
    """Barra de progreso por pasos (1 = primero)."""
    partes = []
    for i, n in enumerate(nombres, start=1):
        estado = "hecho" if i < actual else ("activo" if i == actual else "")
        num = icono("check", 15, "#15803D", 3) if i < actual else str(i)
        if i > 1:
            partes.append(f"<div class='raya {'hecha' if i <= actual else ''}'></div>")
        partes.append(f"<div class='paso {estado}'><span class='n'>{num}</span><b>{escape(n)}</b></div>")
    st.markdown("<div class='pasos'>" + "".join(partes) + "</div>", unsafe_allow_html=True)
