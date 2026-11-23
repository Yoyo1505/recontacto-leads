import pandas as pd

from recontacto.data import cargar_leads
from conftest import fila


def test_fechas_en_dos_formatos_se_normalizan(escribir):
    ruta = escribir([
        fila("L1", "55-01000001", fecha="2026-10-01 10:00", contacto="2026-10-01 11:00"),
        fila("L2", "55-01000002", fecha="02/10/2026 09:30", contacto="02/10/2026 10:00"),
    ])
    df = cargar_leads(ruta)
    assert df["fecha_registro"].tolist() == [pd.Timestamp("2026-10-01 10:00"), pd.Timestamp("2026-10-02 09:30")]
    assert df["primer_contacto"].iloc[1] == pd.Timestamp("2026-10-02 10:00")


def test_contacto_vacio_es_nulo_y_sin_intentos(escribir):
    ruta = escribir([fila("L1", "55-01000001", contacto="", resultado="sin_contactar")])
    df = cargar_leads(ruta)
    assert df["primer_contacto"].isna().all()
    assert df["intentos_previos"].iloc[0] == 0


def test_telefono_repetido_marca_duplicado_y_conserva_el_primero(escribir):
    ruta = escribir([
        fila("L1", "55-01000001", fecha="2026-10-01 10:00"),
        fila("L2", "55-01000001", fecha="2026-10-05 10:00", contacto="2026-10-05 11:00"),
    ])
    df = cargar_leads(ruta)
    assert df["es_duplicado"].tolist() == [False, True]
    assert df["intentos_previos"].tolist() == [2, 2]


def test_cliente_se_propaga_a_los_registros_del_mismo_telefono(escribir):
    ruta = escribir([
        fila("L1", "55-01000001", resultado="venta", monto="1299"),
        fila("L2", "55-01000001", fecha="2026-10-05 10:00", contacto="2026-10-05 11:00"),
    ])
    df = cargar_leads(ruta)
    assert df["ya_es_cliente"].all()


def test_rechazo_y_seguimiento_se_propagan(escribir):
    ruta = escribir([
        fila("L1", "55-01000001", resultado="no_interesado"),
        fila("L2", "55-01000001", fecha="2026-10-05 10:00"),
        fila("L3", "55-01000002", resultado="en_seguimiento"),
    ])
    df = cargar_leads(ruta)
    assert df.loc[df["telefono"] == "55-01000001", "telefono_rechazo"].all()
    assert df.loc[df["telefono"] == "55-01000002", "telefono_en_seguimiento"].all()


def test_edad_invalida_pasa_a_nulo(escribir):
    ruta = escribir([
        fila("L1", "55-01000001", edad="199"),
        fila("L2", "55-01000002", edad="3"),
        fila("L3", "55-01000003", edad="35"),
    ])
    df = cargar_leads(ruta)
    assert df["edad"].isna().tolist() == [True, True, False]
    assert df["edad_valida"].tolist() == [False, False, True]


def test_datos_reales_cantidades_conocidas(df_real):
    assert len(df_real) == 1811
    assert int(df_real["es_duplicado"].sum()) == 70
    assert int((~df_real["edad_valida"]).sum()) == 14
    assert df_real["fecha_registro"].notna().all()
