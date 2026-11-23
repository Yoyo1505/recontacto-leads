import numpy as np
import pandas as pd

from dataclasses import replace

from recontacto import config, evaluation, features, mensajes, pipeline, policy
from recontacto.model import ModeloContacto

AHORA = config.HOY_SIMULADO


def test_probabilidades_en_rango(modelo_real):
    modelo, X, _ = modelo_real
    p = modelo.probabilidad(X)
    assert ((p >= 0) & (p <= 1)).all()


def test_contribuciones_suman_la_diferencia_en_logit(modelo_real):
    modelo, X, _ = modelo_real
    muestra = X.sample(50, random_state=1)
    aportes = modelo.contribuciones(muestra)
    clasificador = modelo.pipeline.named_steps["clf"]
    logit = clasificador.decision_function(modelo.pipeline.named_steps["pre"].transform(muestra[modelo.columnas]))
    logit_medio = clasificador.decision_function(modelo.media_.reshape(1, -1))[0]
    assert np.allclose(aportes.sum(axis=1).to_numpy(), logit - logit_medio, atol=1e-8)


def test_tipo_de_modelo_desconocido_falla():
    try:
        ModeloContacto("otro")
    except ValueError:
        return
    raise AssertionError("debio fallar")


def test_evaluacion_no_mezcla_entrenamiento_y_prueba(df_real):
    X, y = features.desde_contactos(df_real)
    X_tr, _, X_te, _ = evaluation.dividir_en_el_tiempo(X, y, config.FECHA_CORTE_EVALUACION)
    assert X_tr["fecha_registro"].max() < pd.Timestamp(config.FECHA_CORTE_EVALUACION)
    assert X_te["fecha_registro"].min() >= pd.Timestamp(config.FECHA_CORTE_EVALUACION)


def test_el_modelo_supera_a_la_tasa_constante(df_real):
    resultados, _, _ = evaluation.evaluar_modelos(df_real)
    assert resultados["logistica"]["auc"] > 0.5
    assert resultados["logistica"]["auc_ic95"][0] > 0.5
    assert resultados["logistica"]["brier"] <= resultados["constante"]["brier"]


def _lista(df_real, modelo_real, **kwargs):
    modelo = modelo_real[0]
    return pipeline.generar_lista(df_real, modelo, AHORA, **kwargs)


def test_la_lista_no_incluye_a_quien_no_debe_contactarse(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real)
    prohibidos = df_real[
        df_real["ya_es_cliente"] | df_real["telefono_rechazo"] | df_real["telefono_en_seguimiento"] | df_real["es_duplicado"]
    ]["lead_id"]
    assert not set(lista["lead_id"]) & set(prohibidos)
    assert lista["lead_id"].is_unique


def test_horarios_respetan_reglas_y_capacidad(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real, reglas=replace(config.REGLAS, capacidad_por_hora=10))
    asignados = lista[lista["accion"] == "contactar"]
    horarios = asignados["horario_asignado"]
    assert (horarios.dt.weekday != 6).all()
    assert horarios.dt.hour.between(config.REGLAS.horas_permitidas[0], config.REGLAS.horas_permitidas[-1]).all()
    assert (horarios > pd.Timestamp(AHORA)).all()
    assert asignados.groupby("horario_asignado").size().max() <= 10


def test_nunca_contactados_van_primero_y_el_mismo_dia(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real)
    nunca = lista[lista["nunca_contactado"]]
    assert lista["nunca_contactado"].iloc[: len(nunca)].all()
    assert (nunca["horario_asignado"].dt.date == AHORA.date()).all()


def test_quien_no_cabe_queda_en_cola_y_no_se_descarta(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real, reglas=replace(config.REGLAS, capacidad_por_hora=1))
    assert (lista["accion"] == "en_cola").any()
    en_cola = lista[lista["accion"] == "en_cola"]
    assert en_cola["horario_asignado"].isna().all()
    assert (en_cola["mensaje"] == "").all()


def test_mensajes_de_la_lista_son_validos_y_tienen_motivo(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real)
    asignados = lista[lista["accion"] == "contactar"]
    assert asignados["motivo"].str.len().gt(10).all()
    for texto in asignados["mensaje"]:
        assert mensajes.validar_mensaje(texto).valido


def test_la_lista_es_determinista(df_real, modelo_real):
    primera, _ = _lista(df_real, modelo_real)
    segunda, _ = _lista(df_real, modelo_real)
    pd.testing.assert_frame_equal(primera, segunda)


def test_excluidos_traen_motivo_legible(df_real, modelo_real):
    _, excluidos = _lista(df_real, modelo_real)
    assert set(excluidos["motivo_exclusion"]) <= set(policy.MOTIVOS)
    assert excluidos["motivo"].notna().all()
