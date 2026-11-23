from dataclasses import replace

import pandas as pd
import pytest

from recontacto import config, mensajes, pipeline
from recontacto.config import REGLAS, Reglas

AHORA = config.HOY_SIMULADO


def _lista(df, modelo, **cambios):
    return pipeline.generar_lista(df, modelo, AHORA, replace(REGLAS, **cambios))


@pytest.mark.parametrize(
    "cambios",
    [
        {"hora_inicio": 20, "hora_fin": 9},
        {"hora_inicio": -1},
        {"hora_fin": 25},
        {"dias_permitidos": ()},
        {"dias_permitidos": (7,)},
        {"max_intentos": 0},
        {"capacidad_por_hora": 0},
        {"ventana_dias": 0},
        {"horas_entre_intentos": -1},
    ],
)
def test_reglas_invalidas_se_rechazan(cambios):
    with pytest.raises(ValueError):
        Reglas(**cambios)


def test_reglas_por_defecto_son_validas():
    assert REGLAS.horas_permitidas == tuple(range(9, 20))


def test_cambio_no_llamar_antes_de_las_10(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real[0], hora_inicio=10)
    asignados = lista[lista["accion"] == "contactar"]
    assert asignados["horario_asignado"].dt.hour.min() >= 10


def test_cambio_quitar_el_sabado(df_real, modelo_real):
    dias = (0, 1, 2, 3, 4)
    lista, _ = _lista(df_real, modelo_real[0], dias_permitidos=dias)
    asignados = lista[lista["accion"] == "contactar"]
    assert set(asignados["horario_asignado"].dt.weekday) <= set(dias)


def test_cambio_maximo_dos_intentos_excluye_a_quien_ya_tiene_dos(df_real, modelo_real):
    base, _ = _lista(df_real, modelo_real[0])
    menos, excluidos = _lista(df_real, modelo_real[0], max_intentos=2)
    assert len(menos) < len(base)
    assert (menos["intento"] <= 2).all()
    assert "max_intentos" in set(excluidos["motivo_exclusion"])


def test_ultimo_intento_cambia_el_mensaje(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real[0], max_intentos=2)
    asignados = lista[(lista["accion"] == "contactar") & (lista["intento"] == 2)]
    assert len(asignados) > 0
    assert asignados["mensaje"].str.contains("último mensaje").all()


def test_cambio_ventana_mas_corta_reduce_candidatos(df_real, modelo_real):
    base, _ = _lista(df_real, modelo_real[0])
    corta, _ = _lista(df_real, modelo_real[0], ventana_dias=7)
    assert len(corta) < len(base)
    assert (corta["dias_desde_registro"] <= 7).all()


def test_cambio_capacidad_de_ocho(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real[0], capacidad_por_hora=8)
    asignados = lista[lista["accion"] == "contactar"]
    assert asignados.groupby("horario_asignado").size().max() <= 8


def test_cambio_mas_horas_entre_intentos_no_asigna_antes(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real[0], horas_entre_intentos=72)
    asignados = lista[(lista["accion"] == "contactar") & (~lista["nunca_contactado"])]
    ultimos = df_real.set_index("lead_id")["ultimo_contacto"].reindex(asignados["lead_id"]).to_numpy()
    espera = asignados["horario_asignado"].to_numpy() - ultimos
    assert (espera >= pd.Timedelta(hours=72)).all()


def test_todos_los_mensajes_siguen_siendo_validos_con_otras_reglas(df_real, modelo_real):
    lista, _ = _lista(df_real, modelo_real[0], max_intentos=2, hora_inicio=11, capacidad_por_hora=5)
    for texto in lista.loc[lista["accion"] == "contactar", "mensaje"]:
        assert mensajes.validar_mensaje(texto).valido
