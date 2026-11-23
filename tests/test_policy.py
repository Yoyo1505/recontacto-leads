from dataclasses import replace
from datetime import datetime

import pandas as pd

from recontacto import config, policy
from recontacto.data import cargar_leads
from conftest import fila

AHORA = datetime(2026, 10, 10, 8, 0)


def test_horarios_validos_respetan_ventana_y_dias():
    horarios = policy.horarios_validos(AHORA, replace(config.REGLAS, horizonte_dias=7))
    assert horarios
    assert all(h.weekday() != 6 for h in horarios)
    assert all(h.hour in config.REGLAS.horas_permitidas for h in horarios)
    assert all(h > AHORA for h in horarios)


def test_horarios_validos_saltan_el_domingo():
    sabado_noche = datetime(2026, 10, 10, 21, 0)
    horarios = policy.horarios_validos(sabado_noche, replace(config.REGLAS, horizonte_dias=2))
    assert min(horarios).weekday() == 0
    assert min(horarios).hour == config.REGLAS.horas_permitidas[0]


def _motivos(escribir, filas):
    df = cargar_leads(escribir(filas))
    return policy.evaluar_elegibilidad(df, AHORA).set_index("lead_id")["motivo_exclusion"]


def test_lead_normal_es_elegible(escribir):
    motivos = _motivos(escribir, [fila("L1", "55-01000001", fecha="2026-10-08 10:00", contacto="2026-10-08 11:00")])
    assert pd.isna(motivos["L1"])


def test_cliente_rechazo_seguimiento_y_duplicado_se_excluyen(escribir):
    motivos = _motivos(escribir, [
        fila("L1", "55-01000001", fecha="2026-10-08 10:00", resultado="venta", monto="1299"),
        fila("L2", "55-01000002", fecha="2026-10-08 10:00", resultado="no_interesado"),
        fila("L3", "55-01000003", fecha="2026-10-08 10:00", resultado="en_seguimiento"),
        fila("L4", "55-01000004", fecha="2026-10-07 10:00"),
        fila("L5", "55-01000004", fecha="2026-10-08 10:00"),
    ])
    assert motivos["L1"] == "cliente"
    assert motivos["L2"] == "rechazo"
    assert motivos["L3"] == "en_seguimiento"
    assert pd.isna(motivos["L4"])
    assert motivos["L5"] == "duplicado"


def test_cliente_con_registro_repetido_excluye_ambos(escribir):
    motivos = _motivos(escribir, [
        fila("L1", "55-01000001", fecha="2026-10-07 10:00", resultado="venta", monto="1299"),
        fila("L2", "55-01000001", fecha="2026-10-08 10:00"),
    ])
    assert motivos["L1"] == "cliente"
    assert motivos["L2"] == "duplicado"


def test_fuera_de_ventana_de_recuperacion(escribir):
    motivos = _motivos(escribir, [fila("L1", "55-01000001", fecha="2026-08-01 10:00", contacto="2026-08-01 11:00")])
    assert motivos["L1"] == "fuera_ventana"


def test_maximo_de_intentos(escribir):
    filas = [
        fila(f"L{i}", "55-01000001", fecha=f"2026-10-0{i} 10:00", contacto=f"2026-10-0{i} 11:00")
        for i in (5, 6, 7)
    ]
    df = cargar_leads(escribir(filas))
    evaluado = policy.evaluar_elegibilidad(df, AHORA)
    primero = evaluado[~evaluado["es_duplicado"]].iloc[0]
    assert primero["motivo_exclusion"] == "max_intentos"


def test_primer_horario_respeta_espera_entre_intentos():
    ultimo = pd.Timestamp("2026-10-09 18:00")
    minimo = policy.primer_horario_permitido(ultimo, AHORA)
    assert minimo == pd.Timestamp("2026-10-10 18:00")
    assert policy.primer_horario_permitido(pd.NaT, AHORA) == pd.Timestamp(AHORA)
