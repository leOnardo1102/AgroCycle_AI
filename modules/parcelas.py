"""Gestión de agricultores y parcelas (RF-01, RF-02, RF-04, RF-05, RF-06)."""
import json

from sqlalchemy import select

from database.conexion import sesion
from database.modelos import Agricultor, Parcela
from utils.validaciones import validar_agricultor, validar_parcela

CAMPOS = ["nombre", "latitud", "longitud", "superficie", "disponibilidad_agua", "pendiente",
          "observaciones", "ph", "textura", "materia_organica", "poligono", "drenaje"]
CAMPOS_AGRICULTOR = ["nombre", "documento", "comunidad", "telefono", "correo"]


class DatosInvalidos(ValueError):
    def __init__(self, errores: list[str]):
        super().__init__("; ".join(errores))
        self.errores = errores


def obtener_o_crear_agricultor(nombre: str) -> Agricultor:
    nombre = nombre.strip() or "Agricultor"
    with sesion() as s:
        a = s.scalar(select(Agricultor).where(Agricultor.nombre == nombre))
        if not a:
            a = Agricultor(nombre=nombre)
            s.add(a)
            s.flush()
        return a


def registrar_agricultor(datos: dict) -> Agricultor:
    """Alta de un agricultor en la cartera del técnico."""
    datos = {k: (str(datos.get(k) or "").strip() or None) for k in CAMPOS_AGRICULTOR}
    errores = validar_agricultor(datos)
    with sesion() as s:
        if datos["documento"] and s.scalar(select(Agricultor).where(Agricultor.documento == datos["documento"])):
            errores.append("Ya existe un agricultor con esa cédula.")
        if errores:
            raise DatosInvalidos(errores)
        a = Agricultor(**datos)
        s.add(a)
        s.flush()
        return a


def editar_agricultor(id_agricultor: int, datos: dict) -> Agricultor:
    datos = {k: (str(datos.get(k) or "").strip() or None) for k in CAMPOS_AGRICULTOR}
    errores = validar_agricultor(datos)
    if errores:
        raise DatosInvalidos(errores)
    with sesion() as s:
        a = s.get(Agricultor, id_agricultor)
        for k, v in datos.items():
            setattr(a, k, v)
        return a


def obtener_agricultor(id_agricultor: int) -> Agricultor | None:
    with sesion() as s:
        return s.get(Agricultor, id_agricultor)


def listar_agricultores() -> list[Agricultor]:
    with sesion() as s:
        return list(s.scalars(select(Agricultor).order_by(Agricultor.nombre)))


def registrar(id_agricultor: int, datos: dict) -> Parcela:
    errores = validar_parcela(datos)
    if errores:
        raise DatosInvalidos(errores)
    with sesion() as s:
        p = Parcela(id_agricultor=id_agricultor, problemas=json.dumps(datos.get("problemas", [])),
                    **{k: datos.get(k) for k in CAMPOS})
        s.add(p)
        s.flush()
        return p


def editar(id_parcela: int, datos: dict) -> Parcela:
    actual = obtener(id_parcela)
    combinados = {k: getattr(actual, k) for k in CAMPOS} | datos
    errores = validar_parcela(combinados)
    if errores:
        raise DatosInvalidos(errores)
    with sesion() as s:
        p = s.get(Parcela, id_parcela)
        for k in CAMPOS:
            if k in datos:
                setattr(p, k, datos[k])
        if "problemas" in datos:
            p.problemas = json.dumps(datos["problemas"])
        return p


def obtener(id_parcela: int) -> Parcela | None:
    with sesion() as s:
        return s.get(Parcela, id_parcela)


def listar(id_agricultor: int) -> list[Parcela]:
    with sesion() as s:
        return list(s.scalars(select(Parcela).where(Parcela.id_agricultor == id_agricultor).order_by(Parcela.nombre)))


def eliminar(id_parcela: int) -> None:
    with sesion() as s:
        p = s.get(Parcela, id_parcela)
        if p:
            s.delete(p)
