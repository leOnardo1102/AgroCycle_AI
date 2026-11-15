"""Idioma de la interfaz (Español / English).

La app está escrita en español. Cuando el usuario elige «English», esta capa traduce en el momento de
mostrar cada texto (títulos, botones, etiquetas, tarjetas HTML, tablas y gráficos) usando el diccionario
de ui/traducciones_en.py. En español no cambia nada.

Cómo funciona:
- `instalar()` envuelve una sola vez los métodos de Streamlit que muestran texto.
- `tr(texto)` traduce: primero frase exacta, luego plantillas con datos variables (números, meses,
  cultivos) y, en textos con HTML o varias líneas, cada fragmento por separado.
- Lo que no está en el diccionario se muestra en español y, con AGROCYCLE_I18N_LOG=1, se anota en
  logs/i18n_faltantes.txt para completarlo después.
"""
from __future__ import annotations

import functools
import os
import re
from pathlib import Path

import streamlit as st

IDIOMAS = {"es": "Español", "en": "English"}
_FALTANTES: set[str] = set()
_LOG = os.environ.get("AGROCYCLE_I18N_LOG") == "1"


# ------------------------------------------------------------------ idioma activo
def idioma() -> str:
    try:
        return st.session_state.get("idioma", "es")
    except Exception:  # fuera de una sesión de Streamlit (pruebas, PDF)
        return "es"


def en_ingles() -> bool:
    return idioma() == "en"


def iniciar_idioma():
    """Toma el idioma de la URL (?lang=en) la primera vez y lo mantiene en la sesión."""
    ss = st.session_state
    if "idioma" not in ss:
        q = str(st.query_params.get("lang", "es")).lower()
        ss.idioma = "en" if q.startswith("en") else "es"


def selector():
    """Control ES | EN para la barra lateral; deja el idioma también en la URL para poder compartirla."""
    ss = st.session_state
    elegido = st.segmented_control("Idioma", ["es", "en"], default=ss.idioma, format_func=lambda k: {"es": "Español", "en": "English"}[k],
                                   label_visibility="collapsed", key="idioma_ctrl", width="stretch")
    if elegido and elegido != ss.idioma:
        ss.idioma = elegido
        st.query_params["lang"] = elegido
        st.rerun()


# ------------------------------------------------------------------ traducción
_ETIQUETA = re.compile(r"(<[^>]+>)")
_ESPACIOS = re.compile(r"^(\s*)(.*?)(\s*)$", re.S)


@functools.lru_cache(maxsize=1)
def _dic():
    from ui import traducciones_en as T
    exactas = {k.strip(): v for k, v in T.EXACTAS.items()}
    reglas = [(re.compile(p, re.S), r) for p, r in T.PLANTILLAS]
    palabras = T.PALABRAS
    return exactas, reglas, palabras


def _palabra(s: str) -> str:
    """Traduce valores sueltos que van dentro de plantillas (meses, cultivos, niveles)."""
    exactas, _, palabras = _dic()
    s2 = s.strip()
    if s2 in exactas:
        return exactas[s2]
    if s2 in palabras:
        return palabras[s2]
    m = re.match(r"^([^\wÁÉÍÓÚÑáéíóúñ]+\s*)(.+)$", s2)
    if m and m.group(2) != s2:  # «🫛 Haba»
        t2 = _palabra(m.group(2))
        if t2 != m.group(2):
            return m.group(1) + t2
    # listas «a, b y c»
    if "," in s2 or " y " in s2:
        partes = re.split(r"(,\s*|\s+y\s+)", s2)
        out = []
        for p in partes:
            if re.fullmatch(r",\s*", p):
                out.append(p)
            elif re.fullmatch(r"\s+y\s+", p):
                out.append(" and ")
            else:
                out.append(_palabra(p) if p.strip() else p)
        return "".join(out)
    return s


def _plantillas(s: str) -> str | None:
    _, reglas, _ = _dic()
    for patron, repl in reglas:
        m = patron.fullmatch(s)
        if m:
            if callable(repl):
                return repl(m, _palabra)
            g = {k: _palabra(v) if isinstance(v, str) else v for k, v in m.groupdict().items()}
            return repl.format(**{k: (v if v is not None else "") for k, v in g.items()})
    return None


_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_ORD = re.compile(r"\b(\d+)(?:ro|do|er|to|vo|no|mo|ra|da|ta)\b")


def ordinal(n) -> str:
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def numero_en(x: str) -> str:
    """2.694 → 2,694 · 0,58 → 0.58 (formato inglés)."""
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", x):
        return x.replace(".", ",")
    if re.fullmatch(r"\d+,\d+", x):
        return x.replace(",", ".")
    return x


def _con_numeros(s: str) -> str | None:
    """Frases con cifras: en el diccionario se escriben con # en lugar de cada número (y #º para ordinales)."""
    if not _NUM.search(s):
        return None
    exactas, _, _ = _dic()
    s1 = _ORD.sub(lambda m: m.group(1) + "º", s)
    clave = _NUM.sub("#", s1)
    destino = exactas.get(clave)
    if destino is None:
        return None
    nums = iter(_NUM.findall(s1))
    return re.sub("#º|#", lambda m: ordinal(next(nums, 0)) if m.group(0) == "#º" else numero_en(next(nums, "#")), destino)


def _frase(s: str) -> str:
    """Traduce un fragmento de texto sin HTML."""
    if not s or not s.strip():
        return s
    pre, nucleo, post = _ESPACIOS.match(s).groups()
    exactas, _, palabras = _dic()
    if nucleo in exactas:
        return pre + exactas[nucleo] + post
    if nucleo in palabras:
        return pre + palabras[nucleo] + post
    t = _plantillas(nucleo)
    if t is not None:
        return pre + t + post
    t = _con_numeros(nucleo)
    if t is not None:
        return pre + t + post
    # icono de Material al inicio: «:material/history: Historial»
    m = re.match(r"^(:material/[a-z_]+:\s*)(.+)$", nucleo, re.S)
    if m:
        return pre + m.group(1) + _frase(m.group(2)) + post
    # listas separadas por « · », « → » o «&nbsp;·&nbsp;»
    for sep in ("&nbsp;·&nbsp;", " · ", " → ", " | "):
        if sep in nucleo:
            partes = nucleo.split(sep)
            trad = [_frase(p) for p in partes]
            if trad != partes:
                return pre + sep.join(trad) + post
    # varias líneas (markdown): cada una por separado
    if "\n" in nucleo:
        return pre + "\n".join(_frase(linea) for linea in nucleo.split("\n")) + post
    # viñetas o encabezados markdown
    m = re.match(r"^((?:[-*+]|\d+\.|#{1,6})\s+)(.*)$", nucleo, re.S)
    if m:
        return pre + m.group(1) + _frase(m.group(2)) + post
    # negritas o cursivas que envuelven todo
    m = re.fullmatch(r"(\*\*|\*|_)(.+?)\1(.*)", nucleo, re.S)
    if m and m.group(2).strip() in exactas:
        return pre + m.group(1) + exactas[m.group(2).strip()] + m.group(1) + _frase(m.group(3)) + post
    # icono o emoji al inicio: «🌧️ Lluvias»
    m = re.match(r"^([^\wÁÉÍÓÚÑáéíóúñ¿¡(\[]+\s*)(.+)$", nucleo, re.S)
    if m and m.group(2) != nucleo:
        t2 = _frase(m.group(2))
        if t2 != m.group(2):
            return pre + m.group(1) + t2 + post
    # oraciones separadas por punto
    if re.search(r"[.!?]\s+\S", nucleo):
        partes = re.split(r"(?<=[.!?])(\s+)", nucleo)
        trad = [_frase(p) if not p.isspace() else p for p in partes]
        if trad != partes:
            return pre + "".join(trad) + post
    if _LOG and re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3}", nucleo):
        _anotar(nucleo)
    return s


def _anotar(s: str):
    if s in _FALTANTES:
        return
    _FALTANTES.add(s)
    try:
        p = Path(__file__).resolve().parent.parent / "logs"
        p.mkdir(exist_ok=True)
        with open(p / "i18n_faltantes.txt", "a", encoding="utf-8") as f:
            f.write(s.replace("\n", "\\n") + "\n")
    except Exception:
        pass


def tr(texto):
    """Traduce al idioma activo (sin efecto en español o si no es texto)."""
    if not isinstance(texto, str) or not en_ingles() or not texto.strip():
        return texto
    exactas, _, _ = _dic()
    if texto.strip() in exactas:
        return texto.replace(texto.strip(), exactas[texto.strip()])
    if "<" in texto and ">" in texto:
        partes, salida, codigo = _ETIQUETA.split(texto), [], False
        for p in partes:
            if p.startswith("<") and p.endswith(">"):
                low = p.lower()
                if low.startswith(("<style", "<script")):
                    codigo = True
                elif low.startswith(("</style", "</script")):
                    codigo = False
                salida.append(p)
            else:
                salida.append(p if codigo else _frase(p))
        return "".join(salida)
    return _frase(texto)


def t(texto: str, **datos) -> str:
    """Uso directo en el código: t("Hola {n}", n=3)."""
    s = tr(texto)
    return s.format(**datos) if datos else s


# ------------------------------------------------------------------ envolturas de Streamlit
_ARGS_TEXTO = {  # método: (posiciones a traducir, nombres de argumentos a traducir)
    "markdown": ((0,), ("body", "help")), "write": (None, ()), "caption": ((0,), ("body", "help")),
    "title": ((0,), ("body", "help")), "header": ((0,), ("body", "help")), "subheader": ((0,), ("body", "help")),
    "text": ((0,), ("body", "help")), "info": ((0,), ("body",)), "warning": ((0,), ("body",)),
    "success": ((0,), ("body",)), "error": ((0,), ("body",)), "toast": ((0,), ("body",)),
    "button": ((0,), ("label", "help")), "download_button": ((0,), ("label", "help")),
    "link_button": ((0,), ("label", "help")), "form_submit_button": ((0,), ("label", "help")),
    "page_link": ((), ("label", "help")), "expander": ((0,), ("label",)), "popover": ((0,), ("label", "help")),
    "checkbox": ((0,), ("label", "help")), "toggle": ((0,), ("label", "help")),
    "text_input": ((0,), ("label", "help", "placeholder")), "text_area": ((0,), ("label", "help", "placeholder")),
    "number_input": ((0,), ("label", "help", "placeholder")), "date_input": ((0,), ("label", "help")),
    "time_input": ((0,), ("label", "help")), "slider": ((0,), ("label", "help")),
    "select_slider": ((0,), ("label", "help")), "file_uploader": ((0,), ("label", "help")),
    "selectbox": ((0,), ("label", "help", "placeholder")), "multiselect": ((0,), ("label", "help", "placeholder")),
    "radio": ((0,), ("label", "help", "captions")), "segmented_control": ((0,), ("label", "help")),
    "pills": ((0,), ("label", "help")), "metric": ((0, 1, 2), ("label", "value", "delta", "help")),
    "progress": ((1,), ("text",)), "badge": ((0,), ("label",)), "status": ((0,), ("label",)),
}
_CON_OPCIONES = {"selectbox", "multiselect", "radio", "segmented_control", "pills", "select_slider"}


def _trad_val(v):
    if isinstance(v, str):
        return tr(v)
    if isinstance(v, (list, tuple)) and v and all(isinstance(x, str) for x in v):
        return type(v)(tr(x) for x in v)
    return v


def _envolver(nombre, original):
    pos, nombres = _ARGS_TEXTO.get(nombre, ((), ()))

    @functools.wraps(original)
    def envuelta(self, *args, **kwargs):
        if en_ingles():
            args = list(args)
            idx = range(len(args)) if pos is None else [i for i in pos if i < len(args)]
            for i in idx:
                args[i] = _trad_val(args[i])
            for k in nombres:
                if k in kwargs:
                    kwargs[k] = _trad_val(kwargs[k])
            if nombre in _CON_OPCIONES:
                ff = kwargs.get("format_func", str)
                kwargs["format_func"] = lambda v, _ff=ff: tr(str(_ff(v)))
        return original(self, *args, **kwargs)

    return envuelta


def _envolver_tabs(original):
    @functools.wraps(original)
    def envuelta(self, tabs, *args, **kwargs):
        if en_ingles():
            tabs = [tr(x) for x in tabs]
        return original(self, tabs, *args, **kwargs)
    return envuelta


def _df_en(df):
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            d = df.copy()
            d.columns = [tr(c) if isinstance(c, str) else c for c in d.columns]
            for c in d.columns:
                if d[c].dtype == object or pd.api.types.is_string_dtype(d[c]):
                    d[c] = d[c].map(lambda x: tr(x) if isinstance(x, str) else x)
            if isinstance(d.index, pd.Index) and (d.index.dtype == object or pd.api.types.is_string_dtype(d.index)):
                d.index = [tr(x) if isinstance(x, str) else x for x in d.index]
            return d
    except Exception:
        pass
    return df


def _envolver_tabla(original):
    @functools.wraps(original)
    def envuelta(self, data=None, *args, **kwargs):
        if en_ingles():
            data = _df_en(data)
            cc = kwargs.get("column_config")
            if isinstance(cc, dict):
                kwargs["column_config"] = {tr(k) if isinstance(k, str) else k: v for k, v in cc.items()}
        return original(self, data, *args, **kwargs)
    return envuelta


def _fig_en(fig):
    try:
        fig = fig.__class__(fig)  # copia
        lay = fig.layout
        if lay.title and lay.title.text:
            lay.title.text = tr(lay.title.text)
        for ax in ("xaxis", "yaxis"):
            a = getattr(lay, ax, None)
            if a is not None and a.title and a.title.text:
                a.title.text = tr(a.title.text)
        if lay.legend and lay.legend.title and lay.legend.title.text:
            lay.legend.title.text = tr(lay.legend.title.text)
        for ann in lay.annotations or []:
            if ann.text:
                ann.text = tr(ann.text)
        for tr_ in fig.data:
            if getattr(tr_, "name", None):
                tr_.name = tr(tr_.name)
            for attr in ("x", "y", "theta", "labels", "text", "hovertext", "customdata"):
                v = getattr(tr_, attr, None)
                if v is not None and len(v) and all(isinstance(z, str) for z in v):
                    setattr(tr_, attr, [tr(z) for z in v])
            ht = getattr(tr_, "hovertemplate", None)
            if isinstance(ht, str):
                tr_.hovertemplate = tr(ht)
    except Exception:
        pass
    return fig


def _envolver_plotly(original):
    @functools.wraps(original)
    def envuelta(self, figure_or_data, *args, **kwargs):
        if en_ingles():
            figure_or_data = _fig_en(figure_or_data)
        return original(self, figure_or_data, *args, **kwargs)
    return envuelta


def instalar():
    """Envuelve una sola vez los métodos de Streamlit que muestran texto."""
    from streamlit.delta_generator import DeltaGenerator as DG
    if getattr(DG, "_agro_i18n", False):
        return
    for nombre in _ARGS_TEXTO:
        if hasattr(DG, nombre):
            setattr(DG, nombre, _envolver(nombre, getattr(DG, nombre)))
    DG.tabs = _envolver_tabs(DG.tabs)
    DG.dataframe = _envolver_tabla(DG.dataframe)
    DG.table = _envolver_tabla(DG.table)
    DG.plotly_chart = _envolver_plotly(DG.plotly_chart)
    DG._agro_i18n = True
    # st.markdown, st.button… son métodos ya ligados al contenedor principal: se vuelven a ligar.
    principal = st._main
    for nombre in list(_ARGS_TEXTO) + ["tabs", "dataframe", "table", "plotly_chart"]:
        if hasattr(st, nombre) and hasattr(principal, nombre):
            setattr(st, nombre, getattr(principal, nombre))
    st.spinner = _spinner(st.spinner)


def _spinner(original):
    if getattr(original, "_agro_i18n", False):
        return original

    @functools.wraps(original)
    def envuelta(text="", *args, **kwargs):
        return original(tr(text), *args, **kwargs)
    envuelta._agro_i18n = True
    return envuelta
