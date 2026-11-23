import numpy as np
import pytest

from recontacto import config, control, pipeline
from recontacto import simulacion as sim


@pytest.fixture(scope="module")
def preparacion(df_real, modelo_real):
    modelo, X, y = modelo_real
    modelos = sim.modelos_bootstrap(X, y, n=20)
    elegibles, marco, asignados, _ = pipeline.calcular_asignacion(df_real, modelo, config.HOY_SIMULADO)
    return sim.preparar(elegibles, marco, asignados, modelos), len(asignados)


def test_bootstrap_es_reproducible(modelo_real):
    _, X, y = modelo_real
    a = sim.modelos_bootstrap(X, y, n=3, semilla=1)
    b = sim.modelos_bootstrap(X, y, n=3, semilla=1)
    assert len(a) == 3
    assert np.allclose(a[0].probabilidad(X), b[0].probabilidad(X))


def test_preparacion_tiene_la_forma_esperada(preparacion):
    prep, n_leads = preparacion
    assert prep.p_politica.shape == (20, n_leads)
    assert prep.p_base.shape == prep.p_politica.shape
    assert ((prep.p_politica >= 0) & (prep.p_politica <= 1)).all()


def test_el_horario_asignado_tiene_mayor_probabilidad_que_el_promedio(preparacion):
    prep, _ = preparacion
    assert prep.p_politica.mean() >= prep.p_base.mean()


def test_sin_efecto_causal_no_hay_mejora(preparacion):
    prep, _ = preparacion
    corridas = sim.simular(prep, alpha=0.0, n_sim=3000)
    assert abs(corridas["diferencia"].mean()) < 3


def test_la_mejora_crece_con_alpha(preparacion):
    prep, _ = preparacion
    medias = [sim.simular(prep, a, 2000)["diferencia"].mean() for a in (0.0, 0.5, 1.0)]
    assert medias[0] < medias[1] < medias[2]


def test_resumen_tiene_intervalo_ordenado(preparacion):
    prep, _ = preparacion
    r = sim.resumen(sim.simular(prep, 1.0, 1000))
    assert r["ic_bajo"] <= r["media"] <= r["ic_alto"]
    assert 0 <= r["prob_mejora"] <= 1


def test_sensibilidad_devuelve_un_renglon_por_alpha(preparacion):
    prep, _ = preparacion
    tabla = sim.sensibilidad_alpha(prep, alphas=[0, 0.5, 1], n_sim=300)
    assert tabla["alpha"].tolist() == [0, 0.5, 1]


def test_tamano_de_muestra_coincide_con_el_valor_conocido():
    assert 380 <= sim.tamano_muestra(0.5, 0.1) <= 395


def test_tamano_de_muestra_crece_cuando_el_efecto_es_menor():
    assert sim.tamano_muestra(0.6, 0.02) > sim.tamano_muestra(0.6, 0.05) > sim.tamano_muestra(0.6, 0.1)


@pytest.mark.parametrize("p0, delta", [(0, 0.1), (0.5, 0), (0.95, 0.1)])
def test_tamano_de_muestra_rechaza_entradas_invalidas(p0, delta):
    with pytest.raises(ValueError):
        sim.tamano_muestra(p0, delta)


def test_potencia_alcanza_el_nivel_pedido_con_el_n_calculado():
    n = sim.tamano_muestra(0.6, 0.05, potencia=0.8)
    assert 0.76 <= sim.potencia_simulada(0.6, 0.05, n, sims=6000) <= 0.84


def test_error_tipo_I_se_mantiene_cerca_de_alfa():
    tasa = sim.potencia_simulada(0.6, 0.0, 500, sims=8000)
    assert 0.03 <= tasa <= 0.07


def test_wilson_caso_conocido():
    bajo, alto = control.wilson([5], [10])
    assert bajo[0] == pytest.approx(0.2366, abs=0.002)
    assert alto[0] == pytest.approx(0.7634, abs=0.002)


def test_wilson_se_estrecha_con_mas_datos():
    chico = control.wilson([5], [10])
    grande = control.wilson([500], [1000])
    assert (grande[1] - grande[0]) < (chico[1] - chico[0])


def test_carta_p_tiene_limites_coherentes(df_real):
    c = control.carta_p(df_real)
    assert (c["limite_bajo"] <= c["centro"]).all() and (c["centro"] <= c["limite_alto"]).all()
    assert c["fuera_de_control"].sum() <= 3


def test_embudo_limites_se_cierran_al_crecer_n(df_real):
    _, limites, centro = control.embudo(df_real)
    ancho = limites["alto_95%"] - limites["bajo_95%"]
    assert ancho.iloc[0] > ancho.iloc[-1]
    assert 0 < centro < 1


def test_tasa_de_venta_por_canal_es_probabilidad(df_real):
    tasas = sim.tasa_venta_por_canal(df_real)
    assert ((tasas >= 0) & (tasas <= 1)).all()
    assert tasas["Google"] > tasas["TikTok"]


def test_potencia_analitica_coincide_con_la_simulada():
    analitica = sim.potencia_analitica(0.6, 0.05, 1000)
    simulada = sim.potencia_simulada(0.6, 0.05, 1000, sims=8000)
    assert abs(analitica - simulada) < 0.03


def test_potencia_analitica_es_creciente_en_n():
    valores = [sim.potencia_analitica(0.6, 0.05, n) for n in (200, 800, 3000)]
    assert valores[0] < valores[1] < valores[2]


def test_tasas_por_devuelve_intervalos_validos(modelo_real):
    _, X, y = modelo_real
    t = control.tasas_por(X, y, "canal")
    assert t["n"].sum() == len(y)
    assert ((t["bajo"] <= t["tasa"]) & (t["tasa"] <= t["alto"])).all()
