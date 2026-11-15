"""Pruebas del selector de mapa y de la guía rápida."""
from unittest.mock import MagicMock

from vistas import guia, mapa_parcela


def test_poligono_y_area_vertices():
    # 4 esquinas formando un cuadrado de ~100m x 100m (~1 ha) en Riobamba
    puntos = [
        [-1.6600, -78.6500],
        [-1.6600, -78.6491],
        [-1.6609, -78.6491],
        [-1.6609, -78.6500],
    ]
    pol = mapa_parcela._poligono_de(puntos)
    assert pol["geometry"]["type"] == "Polygon"
    anillo = pol["geometry"]["coordinates"][0]
    assert len(anillo) == 5
    assert anillo[0] == anillo[-1]

    ha = mapa_parcela._area_vertices(puntos)
    assert 0.8 <= ha <= 1.3


def test_contorno_cruzado_detecta_figura_en_ocho():
    # Puntos que se cruzan formando una X / 8
    puntos_cruzados = [
        [-1.6600, -78.6500],
        [-1.6609, -78.6491],
        [-1.6600, -78.6491],
        [-1.6609, -78.6500],
    ]
    assert mapa_parcela.contorno_cruzado(puntos_cruzados) is True

    # Cuadrado normal sin cruce
    puntos_buenos = [
        [-1.6600, -78.6500],
        [-1.6600, -78.6491],
        [-1.6609, -78.6491],
        [-1.6609, -78.6500],
    ]
    assert mapa_parcela.contorno_cruzado(puntos_buenos) is False


def test_confirmar_contorno_y_pendiente():
    ss = {
        "mp_modo": "esquinas",
        "mp_cerrado": False,
        "mp_vertices": [
            [-1.6600, -78.6500],
            [-1.6600, -78.6491],
            [-1.6609, -78.6491],
        ],
    }
    assert mapa_parcela.contorno_pendiente(ss) is True

    ok = mapa_parcela.confirmar_contorno(ss)
    assert ok is True
    assert ss["mp_cerrado"] is True
    assert ss["reg_poligono"] is not None
    assert mapa_parcela.contorno_pendiente(ss) is False


def test_guia_rapida_revisar_apertura(monkeypatch):
    import streamlit as st

    ss = {}
    monkeypatch.setattr(st, "session_state", ss)

    llamado = []
    monkeypatch.setattr(guia, "mostrar", lambda: llamado.append(True))

    # Primera vez: abre sola
    guia.revisar_apertura()
    assert len(llamado) == 1
    assert ss.get("guia_vista") is True

    # Segunda vez sin solicitar: no vuelve a abrir
    guia.revisar_apertura()
    assert len(llamado) == 1

    # Solicitud explícita mediante flag
    ss["abrir_guia"] = True
    guia.revisar_apertura()
    assert len(llamado) == 2
    assert "abrir_guia" not in ss
