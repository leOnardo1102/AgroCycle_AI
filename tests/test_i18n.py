"""Capa de idioma: español sin cambios, inglés traducido, cifras en formato inglés."""
import pandas as pd
import pytest

from ui import i18n


@pytest.fixture
def ingles(monkeypatch):
    monkeypatch.setattr(i18n, "en_ingles", lambda: True)


def test_espanol_no_cambia(monkeypatch):
    monkeypatch.setattr(i18n, "en_ingles", lambda: False)
    assert i18n.tr("Generar mi plan de cultivo") == "Generar mi plan de cultivo"


def test_frases_exactas(ingles):
    assert i18n.tr("Generar mi plan de cultivo") == "Generate my crop plan"
    assert i18n.tr("Parcelas del agricultor") == "Farmer's plots"


def test_cifras_y_ordinales(ingles):
    assert i18n.tr("2.694 m") == "2,694 m"
    assert i18n.tr("1,25 ha") == "1.25 ha"
    assert i18n.tr("1ro Quinua → 2do Haba → 3ro Avena forrajera") == "1st Quinoa → 2nd Faba bean → 3rd Forage oat"


def test_plantillas_con_meses_y_cultivos(ingles):
    assert i18n.tr("Hay riesgo de heladas en julio, agosto, septiembre.") == "Frost risk in July, August, September."
    assert i18n.tr("🫛 Haba tiene riesgo de helada en abril (pérdida estimada 12%).") == "🫛 Faba bean is at risk of frost in April (estimated loss 12%)."


def test_html_conserva_etiquetas_y_css(ingles):
    html = "<style>.x{color:red}</style><div class='kpi'><small>Superficie total</small><b>1,25 ha</b></div>"
    out = i18n.tr(html)
    assert "<style>.x{color:red}</style>" in out and "Total area" in out and "1.25 ha" in out


def test_tablas(ingles):
    df = pd.DataFrame([{"Opción": "Opción A", "Confianza": "Media"}])
    d = i18n._df_en(df)
    assert list(d.columns) == ["Option", "Confidence"] and d.iloc[0].tolist() == ["Option A", "Medium"]


def test_texto_desconocido_queda_igual(ingles):
    assert i18n.tr("Terrono de abajo") == "Terrono de abajo"
