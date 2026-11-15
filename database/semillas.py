"""Tres agricultores de ejemplo en Chimborazo (solo si la base está vacía). Teléfonos y correos son de prueba."""
import json
from datetime import date

from sqlalchemy import func, select

from database.conexion import sesion
from database.modelos import Agricultor, Cultivo, HistorialCultivo, Parcela, Tecnico

EJEMPLOS = [
    {"agricultor": {"nombre": "María Guamán", "documento": "0602345670", "comunidad": "Licto", "telefono": "0991234567", "correo": "maria.guaman@ejemplo.com"},
     "parcela": {"nombre": "Lote de la loma", "latitud": -1.7995, "longitud": -78.6020, "superficie": 0.7, "disponibilidad_agua": "turnos",
                 "pendiente": None, "textura": "francoarenoso", "drenaje": "normal", "problemas": ["gusano_blanco", "erosion"]},
     "historial": [("maiz", date(2025, 1, 1), date(2025, 8, 1)), ("papa", date(2025, 11, 1), date(2026, 5, 1))]},
    {"agricultor": {"nombre": "José Cayambe", "documento": "0603456781", "comunidad": "Quimiag", "telefono": "0987654321", "correo": "jose.cayambe@ejemplo.com"},
     "parcela": {"nombre": "Huerta junto al canal", "latitud": -1.6430, "longitud": -78.5690, "superficie": 1.2, "disponibilidad_agua": "completo",
                 "pendiente": None, "textura": "franco", "drenaje": "normal", "problemas": ["suelo_cansado"]},
     "historial": [("papa", date(2025, 3, 1), date(2025, 9, 1)), ("cebolla", date(2025, 10, 1), date(2026, 3, 1))]},
    {"agricultor": {"nombre": "Rosa Yupanqui", "documento": "0604567891", "comunidad": "Guamote", "telefono": "0998877665", "correo": "rosa.yupanqui@ejemplo.com"},
     "parcela": {"nombre": "Chacra de arriba", "latitud": -1.9340, "longitud": -78.7110, "superficie": 0.5, "disponibilidad_agua": "secano",
                 "pendiente": None, "textura": "francoarenoso", "drenaje": "rapido", "problemas": ["heladas", "falta_agua"]},
     "historial": [("cebada", date(2025, 2, 1), date(2025, 8, 1)), ("papa", date(2025, 11, 1), date(2026, 5, 1))]},
]


TECNICO_EJEMPLO = {"nombre": "Ing. Ana Pérez", "cargo": "Técnica de extensión agrícola", "institucion": "MAG Chimborazo",
                   "canton_parroquia": "Riobamba", "telefono": "0987001122", "correo": "ana.perez@ejemplo.com"}


def cargar_si_vacia() -> bool:
    with sesion() as s:
        if not s.scalar(select(func.count()).select_from(Tecnico)):
            s.add(Tecnico(**TECNICO_EJEMPLO))
        if s.scalar(select(func.count()).select_from(Agricultor)):
            return False
        cult = {c.clave: c.id_cultivo for c in s.scalars(select(Cultivo))}
        for e in EJEMPLOS:
            a = Agricultor(**e["agricultor"])
            s.add(a)
            s.flush()
            datos = dict(e["parcela"])
            p = Parcela(id_agricultor=a.id_agricultor, problemas=json.dumps(datos.pop("problemas")),
                        observaciones="Parcela de ejemplo", **datos)
            s.add(p)
            s.flush()
            for clave, fs, fc in e["historial"]:
                s.add(HistorialCultivo(id_parcela=p.id_parcela, id_cultivo=cult[clave], fecha_siembra=fs, fecha_cosecha=fc))
    return True
