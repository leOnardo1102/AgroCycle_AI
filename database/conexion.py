"""Conexión a la base de datos (capa 3 de la arquitectura).

Por defecto usa SQLite (database/agrocycle.db) para que el MVP funcione sin instalar nada.
Para usar SQL Server, define la variable de entorno DATABASE_URL, por ejemplo:
  mssql+pyodbc://usuario:clave@SERVIDOR/agrocycle?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
(requiere `pip install pyodbc` y el ODBC Driver de Microsoft).
"""
import json
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from database.modelos import Base, Cultivo

RAIZ = Path(__file__).resolve().parent.parent
URL_DEFECTO = f"sqlite:///{(RAIZ / 'database' / 'agrocycle.db').as_posix()}"

_engine = None
_Session = None


def obtener_engine(url: str | None = None):
    global _engine, _Session
    if _engine is None or url:
        url = url or os.getenv("DATABASE_URL", URL_DEFECTO)
        _engine = create_engine(url, future=True)
        _Session = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


@contextmanager
def sesion():
    """Uso: `with sesion() as s: ...` -> confirma al salir o revierte si hay error."""
    obtener_engine()
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _migrar(eng):
    """Agrega a una base existente las columnas nuevas (versiones anteriores del MVP)."""
    insp = inspect(eng)
    with eng.begin() as con:
        for tabla in Base.metadata.sorted_tables:
            if not insp.has_table(tabla.name):
                continue
            actuales = {c["name"] for c in insp.get_columns(tabla.name)}
            for col in tabla.columns:
                if col.name not in actuales and col.nullable:
                    tipo = col.type.compile(dialect=eng.dialect)
                    con.execute(text(f'ALTER TABLE {tabla.name} ADD COLUMN {col.name} {tipo}'))


def inicializar(url: str | None = None, semillas: bool = True):
    """Crea/actualiza las tablas, sincroniza el catálogo de cultivos y carga datos de ejemplo si la base está vacía."""
    eng = obtener_engine(url)
    Base.metadata.create_all(eng)
    _migrar(eng)
    cat = json.loads((RAIZ / "data" / "cultivos.json").read_text(encoding="utf-8"))["cultivos"]
    with sesion() as s:
        existentes = {c.clave: c for c in s.scalars(select(Cultivo))}
        for c in cat:
            if c["id"] not in existentes:
                s.add(Cultivo(clave=c["id"], nombre=c["nombre"], ciclo_dias=c["ciclo_dias"],
                              necesidad_hidrica=c["necesidad_hidrica"], descripcion=c["descripcion"],
                              parametros=json.dumps(c, ensure_ascii=False), personalizado=False))
            else:  # agrega campos nuevos del catálogo sin pisar precios/rendimientos editados
                actual = existentes[c["id"]].params
                faltan = {k: v for k, v in c.items() if k not in actual}
                if faltan:
                    existentes[c["id"]].parametros = json.dumps(actual | faltan, ensure_ascii=False)
    if semillas:
        from database.semillas import cargar_si_vacia
        cargar_si_vacia()
