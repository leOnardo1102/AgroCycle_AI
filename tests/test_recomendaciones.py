"""Pruebas del motor de reglas, puntuación y recomendaciones (14.1, 14.3)."""
from datetime import date

import pytest

from modules import motor_agronomico as motor


def _cat():
    import json
    from pathlib import Path
    d = json.loads((Path(__file__).parent.parent / "data" / "cultivos.json").read_text(encoding="utf-8"))
    return {c["id"]: c for c in d["cultivos"]}


def _ctx(**kw):
    from utils.calculos import clima_estimado, completar_clima
    return motor.Contexto(clima=completar_clima(clima_estimado(2900, 600)), altitud=2900, **kw)


C = _cat()


@pytest.mark.parametrize("seq,regla", [
    (["papa", "papa", "haba", "cebada"], "R01"),
    (["papa", "haba", "papa", "cebada"], "R02"),
    (["cebolla", "ajo", "haba", "cebada"], "R03"),
    (["papa", "cebada", "quinua", "melloco"], "R06"),
])
def test_restricciones_esenciales(seq, regla):
    assert regla in motor.restricciones_incumplidas([C[k] for k in seq], _ctx())


def test_historial_impide_repetir_papa():
    seq = [C[k] for k in ["papa", "haba", "cebada", "quinua"]]
    assert motor.restricciones_incumplidas(seq, _ctx()) == []
    assert "R01" in motor.restricciones_incumplidas(seq, _ctx(historial=[C["papa"]]))
    assert "R02" in motor.restricciones_incumplidas(seq, _ctx(historial=[C["papa"], C["haba"]]))


def test_gusano_blanco_refuerza_descanso_de_papa():
    seq = [C[k] for k in ["papa", "haba", "cebada"]]   # en 3 ciclos la papa vuelve tras 2
    assert motor.restricciones_incumplidas(seq, _ctx()) == []
    assert "R02" in motor.restricciones_incumplidas(seq, _ctx(problemas=["gusano_blanco"]))


def test_encharcamiento_excluye_sensibles():
    seq = [C[k] for k in ["papa", "haba", "cebada", "cebolla"]]
    assert "R07" in motor.restricciones_incumplidas(seq, _ctx(problemas=["encharcamiento"]))


def test_leguminosa_reduce_urea():
    ctx = _ctx()
    con = motor.simular_ciclo(C["maiz"], C["haba"], 0, ctx)
    sin = motor.simular_ciclo(C["maiz"], C["cebada"], 0, ctx)
    assert con["n_aplicar"] == sin["n_aplicar"] - 50 and con["rendimiento_rel"] > sin["rendimiento_rel"]


def test_optimizador_cumple_restricciones_y_prioridades():
    cult = [C[k] for k in ["papa", "haba", "frejol", "maiz", "cebolla", "cebada", "quinua", "chocho"]]
    ctx = _ctx(historial=[C["papa"]])
    suelo = motor.optimizar(cult, ctx, {"suelo": 5, "agua": 1, "clima": 1, "sanidad": 3, "ingresos": 0})
    dinero = motor.optimizar(cult, ctx, {"suelo": 0, "agua": 1, "clima": 1, "sanidad": 1, "ingresos": 5})
    for r in (suelo, dinero):
        assert len(r["alternativas"]) == 3
        for a in r["alternativas"]:
            assert a["restricciones_incumplidas"] == [] and a["secuencia"][0]["id"] != "papa"
    assert suelo["alternativas"][0]["puntajes"]["suelo"] >= dinero["alternativas"][0]["puntajes"]["suelo"]
    assert dinero["alternativas"][0]["margen_anual"] >= suelo["alternativas"][0]["margen_anual"]


def test_generar_explica_y_guarda(parcela):
    from modules import historial, recomendaciones as rec
    cat = {c["id"]: c for c in historial.catalogo()}
    historial.agregar(parcela.id_parcela, {"id_cultivo": cat["papa"]["id_cultivo"], "fecha_siembra": date(2026, 1, 1)})
    r = rec.generar(parcela.id_parcela, rec.Opciones(cultivos=["papa", "haba", "frejol", "maiz", "cebolla"], mes_inicio=10, tipo="rotacion"))
    assert len(r["alternativas"]) == 3 and not r["avisos"]
    a = r["alternativas"][0]
    assert a["explicacion"]["motivos"] and a["explicacion"]["limitaciones"]
    assert a["confianza"]["nivel"] in ("Alta", "Media", "Baja") and a["confianza"]["faltante"]
    ids = rec.guardar(r)
    assert len(rec.listar_planes(parcela.id_parcela)) == len(ids) == 3


def test_simulador_ano_seco_reduce_agua(parcela):
    from modules import recomendaciones as rec
    op = rec.Opciones(cultivos=["papa", "haba", "frejol", "maiz", "cebolla"], mes_inicio=10, tipo="rotacion")
    base = rec.generar(parcela.id_parcela, op)
    sim = rec.simular(parcela.id_parcela, op, base, "seco")
    for f in sim["filas"]:
        assert f["escenario"]["puntajes"]["agua"] <= f["base"]["puntajes"]["agua"]
    assert "hipotético" in sim["aviso"]


def test_sin_alternativas_validas(parcela):
    from modules import recomendaciones as rec
    r = rec.generar(parcela.id_parcela, rec.Opciones(cultivos=["papa", "cebada", "quinua"], n_ciclos=3, tipo="rotacion"))
    assert r["sin_resultado"]  # ninguna leguminosa: no se puede cumplir R06 (CU-03, flujo alternativo)


# ------------------------------------------------------------------ plan anual (12 meses, 3 etapas)
OCHO = ["papa", "haba", "cebada", "quinua", "maiz", "arveja", "avena", "pasto"]


def test_plan_anual_dura_12_meses_en_3_etapas():
    ctx = _ctx(mes_inicio=9)
    r = motor.optimizar_anual([C[k] for k in OCHO], ctx, {"suelo": 3, "agua": 3, "clima": 3, "sanidad": 3, "ingresos": 3})
    assert r["alternativas"]
    for a in r["alternativas"]:
        assert a["meses"] <= 12 and a["meses"] == 12
        assert [c["etapa"] for c in a["secuencia"]] == [1, 2, 3]
        assert [c["ciclo_meses"] for c in a["secuencia"]] == [5, 4, 3]
        assert a["ciclos"][-1]["fin"] == 11  # termina en el mes 12
        assert a["restricciones_incumplidas"] == []


def test_plan_anual_respeta_roles_de_cada_etapa():
    for c in C.values():
        for e in motor.ETAPAS:
            v = motor.variante_anual(c, e, 2900)
            if v:
                assert v["ciclo_meses"] == e["meses"] and v["uso_anual"]
    assert motor.variante_anual(C["avena"], motor.ETAPAS[0], 2900) is None      # la avena forrajera no es cultivo principal
    assert motor.variante_anual(C["papa"], motor.ETAPAS[2], 2900) is None       # la papa no va en verano
    assert motor.variante_anual(C["maiz"], motor.ETAPAS[0], 3200) is None       # choclo precoz solo en zonas más bajas


def test_plan_anual_sin_cultivo_para_verano(parcela):
    from modules import recomendaciones as rec
    r = rec.generar(parcela.id_parcela, rec.Opciones(cultivos=["papa", "haba", "frejol", "maiz", "cebolla"]))
    assert r["sin_resultado"] and "Verano" in r["etapas_sin_cultivo"]


def test_mes_inicio_sugerido():
    from datetime import date
    from modules.recomendaciones import mes_inicio_sugerido
    assert mes_inicio_sugerido(True, date(2026, 11, 14)) == 10   # noviembre: empieza ya
    assert mes_inicio_sugerido(True, date(2026, 4, 1)) == 9      # abril: espera a octubre
    assert mes_inicio_sugerido(False, date(2026, 4, 1)) == 3


def test_plan_guardado_con_tecnico(parcela):
    from modules import recomendaciones as rec, tecnicos
    t = tecnicos.registrar({"nombre": "Ing. Pedro Lema", "cargo": "Extensionista", "institucion": "GAD Chimborazo", "telefono": "0991230000"})
    r = rec.generar(parcela.id_parcela, rec.Opciones(cultivos=OCHO))
    rec.guardar(r, t.id_tecnico)
    planes = rec.listar_planes(parcela.id_parcela)
    assert planes and all(p["id_tecnico"] == t.id_tecnico and p["tipo"] == "anual" for p in planes)


def test_escenario_testigo_evidencia_nasa_y_simulador_smap(parcela):
    from modules import recomendaciones as rec
    op = rec.Opciones(cultivos=OCHO)
    r = rec.generar(parcela.id_parcela, op)
    assert "testigo" in r and r["testigo"]["puntajes"]["suelo"] >= 0
    for alt in r["alternativas"]:
        vs = alt["vs_testigo"]
        assert vs["cultivo_testigo"]
        assert vs["resumen_sencillo"] and vs["resumen_tecnico"]
        assert alt["total"] >= vs["puntaje_testigo"]
        exp = alt["explicacion"]
        assert len(exp["respaldo_satelital"]) >= 3
        assert len(exp["validar_en_campo"]) >= 3

    sim = rec.simular(parcela.id_parcela, op, r, "seco", usar_smap=True)
    assert sim["smap"]["disponible"] is True
    assert sim["gpm"] is not None
    assert len(sim["filas"]) == len(r["alternativas"])

