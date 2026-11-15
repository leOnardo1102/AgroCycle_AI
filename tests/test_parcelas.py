"""Pruebas unitarias: registro de parcelas, historial y validaciones (14.1)."""
from datetime import date

import pytest


def test_registrar_y_consultar(parcela):
    from modules import parcelas
    p = parcelas.obtener(parcela.id_parcela)
    assert p.nombre == "Terreno de abajo" and p.superficie == 0.5
    assert p.lista_problemas == ["gusano_blanco"]
    assert [x.nombre for x in parcelas.listar(p.id_agricultor)] == ["Terreno de abajo"]


def test_validacion_datos_obligatorios(bd):
    from modules import parcelas
    a = parcelas.obtener_o_crear_agricultor("Pedro")
    with pytest.raises(parcelas.DatosInvalidos) as e:
        parcelas.registrar(a.id_agricultor, {"nombre": "", "latitud": 10.0, "longitud": -78.6, "superficie": 0, "disponibilidad_agua": "x"})
    assert len(e.value.errores) == 4  # nombre, fuera de Chimborazo, superficie, agua


def test_editar(parcela):
    from modules import parcelas
    parcelas.editar(parcela.id_parcela, {"superficie": 2.0, "problemas": ["erosion"]})
    p = parcelas.obtener(parcela.id_parcela)
    assert p.superficie == 2.0 and p.lista_problemas == ["erosion"]


def test_historial_ordenado(parcela):
    from modules import historial
    cat = {c["id"]: c for c in historial.catalogo()}
    historial.agregar(parcela.id_parcela, {"id_cultivo": cat["haba"]["id_cultivo"], "fecha_siembra": date(2025, 10, 1)})
    historial.agregar(parcela.id_parcela, {"id_cultivo": cat["papa"]["id_cultivo"], "fecha_siembra": date(2024, 11, 1), "fecha_cosecha": date(2025, 5, 1)})
    assert [c["id"] for c in historial.secuencia_reciente(parcela.id_parcela)] == ["papa", "haba"]


def test_historial_fechas_invalidas(parcela):
    from modules import historial, parcelas
    papa = next(c for c in historial.catalogo() if c["id"] == "papa")
    with pytest.raises(parcelas.DatosInvalidos):
        historial.agregar(parcela.id_parcela, {"id_cultivo": papa["id_cultivo"], "fecha_siembra": date(2025, 6, 1), "fecha_cosecha": date(2025, 1, 1)})


def test_catalogo_cargado(bd):
    from modules import historial
    assert len(historial.catalogo()) == 18  # 16 + avena forrajera + pasto ryegrass/trébol
