"""Validación de datos ingresados por el usuario (CU-01, flujo alternativo)."""
import re

# Límites aproximados de la provincia de Chimborazo (con margen)
LAT_MIN, LAT_MAX = -2.6, -1.2
LON_MIN, LON_MAX = -79.3, -78.3

AGUA = {
    "completo": "Tengo riego siempre",
    "turnos": "Riego a veces / por turnos",
    "secano": "Solo lluvia (sin riego)",
}
# Preguntas del suelo en palabras del agricultor -> clase técnica
TIERRA_SENCILLA = {
    "francoarenoso": "Suelta / arenosa (se desmorona)",
    "franco": "Negra y suave (fácil de trabajar)",
    "arcilloso": "Pesada / barrosa (se pega en las botas)",
}
DRENAJE = {
    "rapido": "Se seca rápido después de llover",
    "normal": "Normal",
    "empoza": "Se empoza el agua cuando llueve",
}
TEXTURAS = {
    "arenoso": "Arenoso", "francoarenoso": "Franco-arenoso", "franco": "Franco",
    "francoarcilloso": "Franco-arcilloso", "arcilloso": "Arcilloso",
}
PROBLEMAS = {
    "erosion": "La lluvia se lleva la tierra (erosión)",
    "gusano_blanco": "Gusano blanco / plagas en la papa",
    "suelo_cansado": "La tierra ya no produce como antes",
    "falta_agua": "Falta agua en el verano",
    "heladas": "Caen heladas",
    "encharcamiento": "Se encharca cuando llueve",
}


def validar_parcela(datos: dict) -> list[str]:
    """Devuelve una lista de errores en lenguaje sencillo. Lista vacía = datos válidos."""
    errores = []
    if not str(datos.get("nombre", "")).strip():
        errores.append("Escribe un nombre para tu parcela (por ejemplo: «Terreno de abajo»).")
    lat, lon = datos.get("latitud"), datos.get("longitud")
    if lat is None or lon is None:
        errores.append("Marca la ubicación de la parcela en el mapa.")
    elif not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        errores.append("La ubicación está fuera de Chimborazo. Revisa el punto en el mapa.")
    sup = datos.get("superficie")
    if sup is None or sup <= 0:
        errores.append("Indica el tamaño aproximado de la parcela.")
    elif sup > 500:
        errores.append("La superficie parece demasiado grande (más de 500 ha). Revisa el valor.")
    if datos.get("disponibilidad_agua") not in AGUA:
        errores.append("Indica si tienes agua de riego.")
    ph = datos.get("ph")
    if ph is not None and not (3.5 <= ph <= 9.5):
        errores.append("El pH debe estar entre 3,5 y 9,5.")
    pend = datos.get("pendiente")
    if pend is not None and not (0 <= pend <= 150):
        errores.append("La pendiente debe estar entre 0 y 150 %.")
    return errores


def validar_historial(datos: dict) -> list[str]:
    errores = []
    if not datos.get("id_cultivo"):
        errores.append("Elige el cultivo que sembraste.")
    fs, fc = datos.get("fecha_siembra"), datos.get("fecha_cosecha")
    if fs and fc and fc < fs:
        errores.append("La fecha de cosecha no puede ser anterior a la de siembra.")
    return errores


def validar_cedula(cedula: str) -> bool:
    """Cédula ecuatoriana: 10 dígitos, provincia 01-24 o 30 y dígito verificador (módulo 10)."""
    if not re.fullmatch(r"\d{10}", cedula or ""):
        return False
    prov = int(cedula[:2])
    if not (1 <= prov <= 24 or prov == 30) or int(cedula[2]) > 5:
        return False
    suma = 0
    for i, d in enumerate(cedula[:9]):
        v = int(d) * (2 if i % 2 == 0 else 1)
        suma += v - 9 if v > 9 else v
    return (10 - suma % 10) % 10 == int(cedula[9])


def telefono_whatsapp(telefono: str | None) -> str | None:
    """Convierte un celular de Ecuador al formato internacional de WhatsApp: 0991234567 -> 593991234567."""
    if not telefono:
        return None
    t = re.sub(r"[^\d]", "", telefono)
    if t.startswith("593") and len(t) == 12:
        return t
    if re.fullmatch(r"09\d{8}", t):
        return "593" + t[1:]
    if re.fullmatch(r"9\d{8}", t):
        return "593" + t
    return None


def validar_agricultor(datos: dict) -> list[str]:
    errores = []
    if len(str(datos.get("nombre", "")).strip()) < 3:
        errores.append("Escribe el nombre completo del agricultor.")
    doc = (datos.get("documento") or "").strip()
    if doc and not validar_cedula(doc):
        errores.append("La cédula no es válida (10 dígitos con dígito verificador).")
    tel = (datos.get("telefono") or "").strip()
    if tel and not telefono_whatsapp(tel):
        errores.append("El celular debe tener el formato 09XXXXXXXX.")
    correo = (datos.get("correo") or "").strip()
    if correo and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", correo):
        errores.append("El correo electrónico no es válido.")
    return errores
