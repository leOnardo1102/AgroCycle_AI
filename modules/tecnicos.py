"""Perfil del técnico agropecuario responsable de los planes."""
import re

from sqlalchemy import select

from database.conexion import sesion
from database.modelos import Tecnico
from modules.parcelas import DatosInvalidos
from utils.validaciones import telefono_whatsapp

CAMPOS = ["nombre", "cargo", "institucion", "canton_parroquia", "telefono", "correo"]


def _limpiar(datos: dict) -> dict:
    return {k: (str(datos.get(k) or "").strip() or None) for k in CAMPOS}


def _validar(d: dict) -> list[str]:
    errores = []
    if not d["nombre"] or len(d["nombre"]) < 3:
        errores.append("Escribe el nombre completo del técnico.")
    if d["telefono"] and not telefono_whatsapp(d["telefono"]):
        errores.append("El celular debe tener el formato 09XXXXXXXX.")
    if d["correo"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", d["correo"]):
        errores.append("El correo electrónico no es válido.")
    return errores


def registrar(datos: dict) -> Tecnico:
    d = _limpiar(datos)
    if e := _validar(d):
        raise DatosInvalidos(e)
    with sesion() as s:
        t = Tecnico(**d)
        s.add(t)
        s.flush()
        return t


def editar(id_tecnico: int, datos: dict) -> Tecnico:
    d = _limpiar(datos)
    if e := _validar(d):
        raise DatosInvalidos(e)
    with sesion() as s:
        t = s.get(Tecnico, id_tecnico)
        for k, v in d.items():
            setattr(t, k, v)
        return t


def obtener(id_tecnico: int | None) -> Tecnico | None:
    if not id_tecnico:
        return None
    with sesion() as s:
        return s.get(Tecnico, id_tecnico)


def listar() -> list[Tecnico]:
    with sesion() as s:
        return list(s.scalars(select(Tecnico).order_by(Tecnico.nombre)))
