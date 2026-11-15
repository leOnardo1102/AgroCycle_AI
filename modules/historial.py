"""Historial de cultivos de cada parcela (RF-03, RN-01) y catálogo de cultivos."""
import json

from sqlalchemy import select

from database.conexion import sesion
from database.modelos import Cultivo, HistorialCultivo
from modules.parcelas import DatosInvalidos
from utils.validaciones import validar_historial


def catalogo(solo_ids: list[str] | None = None) -> list[dict]:
    """Parámetros agronómicos de los cultivos del catálogo (con su id de base de datos)."""
    with sesion() as s:
        out = []
        for c in s.scalars(select(Cultivo).order_by(Cultivo.id_cultivo)):
            p = c.params | {"id_cultivo": c.id_cultivo, "personalizado": c.personalizado}
            if solo_ids is None or p["id"] in solo_ids:
                out.append(p)
        return out


def cultivo_por_id(id_cultivo: int) -> dict:
    with sesion() as s:
        c = s.get(Cultivo, id_cultivo)
        return c.params | {"id_cultivo": c.id_cultivo}


def registrar_cultivo_personalizado(p: dict) -> None:
    clave = "u_" + "".join(ch for ch in p["nombre"].lower() if ch.isalnum())[:30]
    p = p | {"id": clave, "ciclo_dias": int(p["ciclo_meses"]) * 30}
    with sesion() as s:
        if s.scalar(select(Cultivo).where(Cultivo.clave == clave)):
            raise DatosInvalidos([f"Ya existe un cultivo llamado {p['nombre']}."])
        s.add(Cultivo(clave=clave, nombre=p["nombre"], ciclo_dias=p["ciclo_dias"], necesidad_hidrica=p["necesidad_hidrica"],
                      descripcion=p.get("descripcion", ""), parametros=json.dumps(p, ensure_ascii=False), personalizado=True))


def actualizar_parametros(id_cultivo: int, cambios: dict) -> None:
    with sesion() as s:
        c = s.get(Cultivo, id_cultivo)
        c.parametros = json.dumps(c.params | cambios, ensure_ascii=False)


def agregar(id_parcela: int, datos: dict) -> HistorialCultivo:
    errores = validar_historial(datos)
    if errores:
        raise DatosInvalidos(errores)
    with sesion() as s:
        h = HistorialCultivo(id_parcela=id_parcela, id_cultivo=datos["id_cultivo"], fecha_siembra=datos.get("fecha_siembra"),
                             fecha_cosecha=datos.get("fecha_cosecha"), observaciones=datos.get("observaciones"))
        s.add(h)
        s.flush()
        return h


def eliminar(id_historial: int) -> None:
    with sesion() as s:
        h = s.get(HistorialCultivo, id_historial)
        if h:
            s.delete(h)


def listar(id_parcela: int) -> list[dict]:
    """Historial ordenado del más antiguo al más reciente (los registros sin fecha van al final, en orden de ingreso)."""
    with sesion() as s:
        regs = list(s.scalars(select(HistorialCultivo).where(HistorialCultivo.id_parcela == id_parcela)))
        def orden(h):
            f = h.fecha_cosecha or h.fecha_siembra
            return (f.toordinal() if f else 10**9, h.id_historial)
        regs.sort(key=orden)
        return [{"id_historial": h.id_historial, "cultivo": h.cultivo.params | {"id_cultivo": h.id_cultivo},
                 "fecha_siembra": h.fecha_siembra, "fecha_cosecha": h.fecha_cosecha, "observaciones": h.observaciones} for h in regs]


def secuencia_reciente(id_parcela: int, max_items: int = 3) -> list[dict]:
    """Parámetros de los últimos cultivos sembrados, para el motor (RN-01)."""
    return [h["cultivo"] for h in listar(id_parcela)][-max_items:]
