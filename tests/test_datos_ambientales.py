"""Pruebas de integración servicio NASA -> procesamiento (14.2), con respuestas reales guardadas."""
from conftest import cargar


def test_interpretar_nasa_power():
    from services import nasa_power
    meses = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    j = {"geometry": {"coordinates": [-78.6, -1.6, 3003.5]},
         "properties": {"parameter": {"T2M": {m: 11.0 for m in meses}, "T2M_MIN": {m: 3.0 for m in meses},
                                      "T2M_MAX": {m: 20.0 for m in meses}, "PRECTOTCORR": {m: 4.0 for m in meses}}}}
    r = nasa_power.interpretar(j)
    assert r["elev_celda"] == 3003.5 and r["meses"][0]["p"] == 124.0 and r["meses"][1]["p"] == 112.0


def test_nasa_power_con_meses_vacios():
    import pytest
    from services import ServicioNoDisponible, nasa_power
    j = {"properties": {"parameter": {"T2M": {m: -999 for m in nasa_power.MESES}, "PRECTOTCORR": {m: -999 for m in nasa_power.MESES}}}}
    with pytest.raises(ServicioNoDisponible):
        nasa_power.interpretar(j)


def test_soilgrids_unidades():
    from services import soilgrids
    j = {"properties": {"layers": [
        {"name": "phh2o", "unit_measure": {"d_factor": 10}, "depths": [{"values": {"mean": 67}}]},
        {"name": "soc", "unit_measure": {"d_factor": 10}, "depths": [{"values": {"mean": 446}}]},
        {"name": "sand", "unit_measure": {"d_factor": 10}, "depths": [{"values": {"mean": 430}}]},
        {"name": "clay", "unit_measure": {"d_factor": 10}, "depths": [{"values": {"mean": 230}}]}]}}
    r = soilgrids.interpretar(j)
    assert r == {"fuente": "SoilGrids", "ph": 6.7, "materia_organica": 7.7, "arena": 43, "arcilla": 23, "textura": "franco"}


def test_obtener_guarda_en_bd_y_corrige_altitud(parcela):
    from modules import datos_ambientales as amb
    d = amb.obtener(parcela)
    assert not d["avisos"]
    c = amb.clima_parcela(parcela, d)
    # La parcela (2771 m, SRTM) está 232 m más abajo que la celda NASA (3003 m): +1,35 °C
    assert round(c["correccion_t"], 2) == 1.35
    assert c["modo_lluvia"] == "mixta"  # NASA (1397 mm) difiere > 40 % de la referencia de Riobamba (480 mm)
    d2 = amb.obtener(parcela)  # segunda vez: desde la tabla Datos_Ambientales
    assert d2["NASA POWER"]["meses"][0]["p"] == cargar("nasa_power_riobamba.json")["meses"][0]["p"]


def test_fuente_caida_no_bloquea(parcela, monkeypatch):
    from modules import datos_ambientales as amb
    from services import ServicioNoDisponible

    def falla(lat, lon):
        raise ServicioNoDisponible("NASA POWER no respondió (Timeout)")
    monkeypatch.setitem(amb.SERVICIOS, "NASA POWER", falla)
    monkeypatch.setattr(amb, "RESPALDO_NASA", amb.RAIZ / "no_existe.json")  # sin archivo de respaldo
    d = amb.obtener(parcela, forzar=True)
    assert d["NASA POWER"] is None and "NASA POWER no respondió" in d["avisos"][0]
    assert amb.clima_parcela(parcela, d)["fuente"] == "Estimación de referencia"


def test_suelo_prioriza_agricultor(parcela):
    from modules import datos_ambientales as amb
    parcela.ph = 5.2
    s = amb.suelo_parcela(parcela, amb.obtener(parcela))
    assert s["ph"] == 5.2 and s["fuentes"]["ph"] == "agricultor"
    assert s["textura"] == "franco" and s["fuentes"]["textura"] == "SoilGrids"
    assert s["fuentes"]["pendiente"] == "NASA SRTM"


def test_ndvi_gpm_smap_srtm_y_tabla_fusion(parcela):
    from services import ndvi, srtm, gpm, smap
    from modules import datos_ambientales as amb, lenguaje_sencillo as ls, simulador

    # 1. NDVI climatológico de Chimborazo [0.15, 0.85] y detección de suelo desnudo jul-sep
    n = ndvi.consultar(parcela.latitud, parcela.longitud, mes_actual=7, altitud=2900)
    assert ndvi.MIN_NDVI <= n["ndvi_min"] <= n["ndvi_max"] <= ndvi.MAX_NDVI
    assert len(n["curva_estacional"]) == 12
    assert {6, 7, 8} <= set(n["meses_suelo_desnudo"])
    assert n["riesgo_erosion_ndvi"] in {"medio", "alto"}
    assert ndvi.clasificar_ndvi(0.20) == "suelo_desnudo"
    assert ndvi.clasificar_ndvi(0.75) == "vegetacion_densa"

    # 2. SRTM pendiente -> riesgo erosión en ladera y LS
    lad_baja = srtm.evaluar_erosion_ladera(3.5)
    lad_alta = srtm.evaluar_erosion_ladera(18.0)
    assert lad_baja["riesgo_erosion_ladera"] == "bajo"
    assert lad_alta["riesgo_erosion_ladera"] == "alto" and lad_alta["factor_ls"] > lad_baja["factor_ls"]

    # 3. GPM lluvias intensas y riesgo de lavado
    gp = gpm.consultar(parcela.latitud, parcela.longitud, pendiente=18.0)
    assert len(gp["frecuencia_mensual_intensa"]) == 12 and gp["dias_lluvia_intensa_anual"] > 0
    assert gp["riesgo_lavado"] in {"moderado", "alto"}

    # 4. SMAP humedad superficial, anomalía hídrica y conexión con simulador
    sm_def = smap.consultar(parcela.latitud, parcela.longitud, mes_actual=7)  # agosto (seco)
    assert sm_def["estado_hidrico"] == "deficit" and sm_def["anomalia_hidrica_pct"] < -8
    diag_def = simulador.diagnosticar_smap(sm_def)
    assert diag_def["escenario_sugerido"] == "seco"

    sm_exc = smap.consultar(parcela.latitud, parcela.longitud, mes_actual=3)  # abril (lluvioso)
    assert sm_exc["estado_hidrico"] == "exceso" and sm_exc["escenario_sugerido"] == "lluvioso"

    meses_base = [{"p": 100.0, "t": 12.0, "tmin": 6.0, "tmax": 18.0} for _ in range(12)]
    meses_adj = simulador.aplicar_smap(meses_base, sm_def)
    assert meses_adj[0]["p"] < meses_base[0]["p"]

    # 5. Persistencia en BD y diagnóstico sencillo sin jerga + tabla multiescala
    d = amb.obtener(parcela)
    assert d["NASA NDVI"] and d["NASA GPM"] and d["NASA SMAP"]
    reconsulta = amb.obtener(parcela)
    assert reconsulta["fechas"]["NASA NDVI"] is not None
    diag_s = amb.diagnostico(parcela, amb.clima_parcela(parcela, d), amb.suelo_parcela(parcela, d), [], sencillo=True)
    assert any(c["titulo"] == "Cobertura de la tierra" for c in diag_s)
    texto_diag = " ".join(c["titulo"] + " " + c["texto"] for c in diag_s)
    assert ls.tiene_jerga(texto_diag) == []
    assert len(amb.TABLA_FUSION_ESCALAS) == 6
    assert any("SRTM" in fila["Fuente satelital"] for fila in amb.TABLA_FUSION_ESCALAS)

