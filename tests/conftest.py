"""Configuración común de las pruebas: base de datos temporal y servicios NASA simulados
con respuestas REALES guardadas en tests/datos (no se necesita internet)."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DATOS = Path(__file__).parent / "datos"


def cargar(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


@pytest.fixture
def bd(tmp_path, monkeypatch):
    from database import conexion
    conexion._engine = None
    conexion.inicializar(f"sqlite:///{(tmp_path / 'prueba.db').as_posix()}")
    from modules import datos_ambientales
    monkeypatch.setitem(datos_ambientales.SERVICIOS, "NASA POWER", lambda la, lo: cargar("nasa_power_riobamba.json"))
    monkeypatch.setitem(datos_ambientales.SERVICIOS, "NASA SRTM", lambda la, lo: cargar("srtm_riobamba.json"))
    monkeypatch.setitem(datos_ambientales.SERVICIOS, "SoilGrids", lambda la, lo: cargar("soilgrids_guano.json"))
    yield conexion
    conexion._engine = None


@pytest.fixture
def parcela(bd):
    from modules import parcelas
    a = parcelas.obtener_o_crear_agricultor("Agricultor de Prueba")
    return parcelas.registrar(a.id_agricultor, {"nombre": "Terreno de abajo", "latitud": -1.664, "longitud": -78.654,
                                                "superficie": 0.5, "disponibilidad_agua": "turnos", "problemas": ["gusano_blanco"]})
