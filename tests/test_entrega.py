"""Pruebas de la cartera, del lenguaje sencillo y del Centro de Entrega al Agricultor."""
import json
import re

import pytest

from modules import entrega, lenguaje_sencillo as ls
from utils.validaciones import telefono_whatsapp, validar_cedula


@pytest.mark.parametrize("entrada,esperado", [("0991234567", "593991234567"), ("099 123 4567", "593991234567"),
                                              ("+593991234567", "593991234567"), ("991234567", "593991234567"),
                                              ("032961234", None), ("", None)])
def test_telefono_ecuador_a_whatsapp(entrada, esperado):
    assert telefono_whatsapp(entrada) == esperado


def test_cedula():
    assert validar_cedula("0602345670") and not validar_cedula("0602345679") and not validar_cedula("9902345670")


def test_semillas_y_cartera(bd):
    from modules import parcelas
    agricultores = parcelas.listar_agricultores()
    assert {a.comunidad for a in agricultores} == {"Licto", "Quimiag", "Guamote"}
    with pytest.raises(parcelas.DatosInvalidos) as e:
        parcelas.registrar_agricultor({"nombre": "Luis Paca", "documento": "0602345670", "telefono": "12345", "correo": "x@"})
    assert len(e.value.errores) == 3  # cédula repetida, celular y correo inválidos
    nuevo = parcelas.registrar_agricultor({"nombre": "Luis Paca", "comunidad": "Calpi", "telefono": "0981112233"})
    assert parcelas.obtener_agricultor(nuevo.id_agricultor).telefono == "0981112233"


def _plan_semilla(comunidad, tipo="anual"):
    from modules import parcelas, recomendaciones as rec
    a = next(x for x in parcelas.listar_agricultores() if x.comunidad == comunidad)
    p = parcelas.listar(a.id_agricultor)[0]
    r = rec.generar(p.id_parcela, rec.Opciones(cultivos=["papa", "haba", "cebada", "quinua", "maiz", "arveja", "avena", "pasto"], mes_inicio=10, tipo=tipo))
    return a, p, r


@pytest.mark.parametrize("comunidad,tipo,pasos", [("Licto", "anual", 3), ("Quimiag", "anual", 3), ("Guamote", "anual", 3),
                                                  ("Licto", "rotacion", 4), ("Guamote", "rotacion", 4)])
def test_guia_sin_jerga_y_con_4_respuestas(bd, comunidad, tipo, pasos):
    a, p, r = _plan_semilla(comunidad, tipo)
    for alt in r["alternativas"]:
        g = alt["guia"]
        assert len(g["pasos"]) == pasos and g["orden"].startswith("1ro ")
        assert g["anual"] == (tipo == "anual")
        assert g["por_que"] and g["ahorro"] and g["clima"]
        assert g["respaldo_nasa"] and g["validar_campo"] and g["vs_testigo"]["resumen_sencillo"]
        html = entrega.html_cartilla(g, a, p)
        textos = (
            json.dumps(g, ensure_ascii=False)
            + entrega.mensaje_whatsapp(g, a, p, "Ing. Ana")
            + entrega.texto_plano(g, a, p)
            + html
        )
        assert ls.tiene_jerga(textos) == [], ls.tiene_jerga(textos)


def test_canales_de_entrega(bd):
    a, p, r = _plan_semilla("Licto")
    g = r["alternativas"][0]["guia"]
    url = entrega.url_whatsapp(a.telefono, entrega.mensaje_whatsapp(g, a, p))
    assert url.startswith("https://wa.me/593991234567?text=")
    assert entrega.url_correo(a.correo, p, "hola").startswith("mailto:maria.guaman@ejemplo.com?subject=")
    h = entrega.html_cartilla(g, a, p, "Ing. Ana")
    from modules import tecnicos
    t = tecnicos.listar()[0]   # técnico de ejemplo
    h = entrega.html_cartilla(g, a, p, t)
    assert "@page{size:A4" in h and "window.print()" in h and "Técnico responsable" in h and t.nombre in h and "MAG Chimborazo" in h
    w = entrega.mensaje_whatsapp(g, a, p, t)
    assert w.rstrip().endswith(t.contacto) and "Tu técnico: Ing. Ana Pérez" in w
    assert "MAG Chimborazo" in entrega.texto_plano(g, a, p, t)
    pdf = entrega.pdf_cartilla(g, a, p, t)
    assert pdf.startswith(b"%PDF") and len(re.findall(rb"/Type\s*/Page[^s]", pdf)) == 1  # una sola hoja


def test_respaldo_nasa_si_falla_y_no_hay_datos(bd, monkeypatch):
    from modules import datos_ambientales as amb, parcelas
    from services import ServicioNoDisponible

    def falla(lat, lon):
        raise ServicioNoDisponible("NASA POWER no respondió (Timeout)")
    monkeypatch.setitem(amb.SERVICIOS, "NASA POWER", falla)
    p = parcelas.listar(parcelas.listar_agricultores()[0].id_agricultor)[0]
    d = amb.obtener(p, forzar=True)
    assert d["NASA POWER"]["fuente"] == "NASA POWER (respaldo Chimborazo)"
    assert amb.clima_parcela(p, d)["fuente"] == "NASA POWER (respaldo Chimborazo)"


def test_migracion_de_base_antigua(tmp_path):
    import sqlite3
    from database import conexion
    db = tmp_path / "vieja.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE agricultor (id_agricultor INTEGER PRIMARY KEY, nombre VARCHAR(120), fecha_registro DATE)")
    con.execute("INSERT INTO agricultor (nombre, fecha_registro) VALUES ('Antiguo', '2026-11-14')")
    con.commit(); con.close()
    conexion._engine = None
    conexion.inicializar(f"sqlite:///{db.as_posix()}")
    cols = {r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(agricultor)")}
    assert {"documento", "comunidad", "telefono", "correo"} <= cols
    conexion._engine = None
