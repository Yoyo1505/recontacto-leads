import csv

import pytest

from recontacto import config
from recontacto.data import cargar_leads
from recontacto.features import desde_contactos
from recontacto.model import ModeloContacto

ENCABEZADO = [
    "lead_id", "fecha_registro", "canal", "anuncio", "estado", "edad", "objetivo",
    "plan_de_interes", "telefono", "asesor", "primer_contacto", "resultado", "monto_venta",
]


def fila(lead_id, telefono, fecha="2026-10-01 10:00", contacto="2026-10-01 11:00", resultado="no_contesta",
         canal="Meta", edad="40", asesor="Asesor A", monto=""):
    return [lead_id, fecha, canal, "Imagen", "CDMX", edad, "control de peso", "1299", telefono,
            asesor if contacto else "", contacto, resultado, monto]


@pytest.fixture
def escribir(tmp_path):
    def _escribir(filas):
        ruta = tmp_path / "leads.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(ENCABEZADO)
            escritor.writerows(filas)
        return ruta
    return _escribir


@pytest.fixture(scope="session")
def df_real():
    return cargar_leads(config.ARCHIVO_LEADS)


@pytest.fixture(scope="session")
def modelo_real(df_real):
    X, y = desde_contactos(df_real)
    return ModeloContacto("logistica").entrenar(X, y), X, y


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATOS", tmp_path)
    monkeypatch.setattr(config, "ARCHIVO_ACTUAL", tmp_path / "leads_actual.csv")
    monkeypatch.setattr(config, "ARCHIVO_BAJAS", tmp_path / "bajas.csv")
    monkeypatch.setattr(config, "HISTORIAL", tmp_path / "historial")
    monkeypatch.setattr(config, "SALIDAS", tmp_path / "salidas")
    return tmp_path
