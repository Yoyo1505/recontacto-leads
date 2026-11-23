"""Versiones y bajas: guarda la base con copia de la anterior, restaura y registra bajas."""

import shutil
from datetime import datetime

import pandas as pd

from .. import config
from ..data import clave_telefono, leer_bajas
from .esquema import COLUMNAS, OPCIONALES, ErrorIngesta


def _formatear_para_guardar(df):
    salida = df.rename(columns={"entidad": "estado"}).copy()
    columnas = [c for c in COLUMNAS if c in salida.columns] + [o for o in OPCIONALES if o in salida.columns]
    salida = salida[columnas]
    for columna in ("fecha_registro", "primer_contacto"):
        salida[columna] = pd.to_datetime(salida[columna]).dt.strftime("%Y-%m-%d %H:%M")
    for columna in ("edad", "plan_de_interes", "monto_venta"):
        numerica = pd.to_numeric(salida[columna], errors="coerce")
        entero = bool((numerica.dropna() % 1 == 0).all())
        salida[columna] = numerica.map(lambda v: "" if pd.isna(v) else (str(int(v)) if entero else str(v)))
    return salida.fillna("")


def guardar_version(df):
    """Guarda la base como `data/leads_actual.csv`. Devuelve el nombre de la copia de la version anterior."""
    config.DATOS.mkdir(exist_ok=True)
    copia = None
    if config.ARCHIVO_ACTUAL.exists():
        config.HISTORIAL.mkdir(exist_ok=True)
        copia = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
        shutil.copy2(config.ARCHIVO_ACTUAL, config.HISTORIAL / copia)
    temporal = config.ARCHIVO_ACTUAL.with_suffix(".tmp")
    _formatear_para_guardar(df).to_csv(temporal, index=False, encoding="utf-8")
    temporal.replace(config.ARCHIVO_ACTUAL)
    for vieja in sorted(config.HISTORIAL.glob("leads_*.csv"))[: -config.VERSIONES_A_CONSERVAR] if config.HISTORIAL.exists() else []:
        vieja.unlink()
    return copia


def aplicar(informe):
    """Guarda lo procesado (y los rechazados, para revisarlos). Falla si no hay nada que guardar."""
    if informe.fusionado is None:
        raise ErrorIngesta("No hay nada que aplicar")
    if len(informe.rechazados):
        config.SALIDAS.mkdir(exist_ok=True)
        informe.rechazados.to_csv(config.SALIDAS / f"rechazados_{datetime.now():%Y%m%d_%H%M%S}.csv", index=False, encoding="utf-8-sig")
    if informe.hay_cambios:
        informe.version_guardada = guardar_version(informe.fusionado)
    informe.aplicado = True
    return informe


def listar_versiones():
    return sorted(p.name for p in config.HISTORIAL.glob("leads_*.csv")) if config.HISTORIAL.exists() else []


def restaurar(nombre=None):
    """Vuelve a una version anterior (la ultima por defecto) o a la base `original`."""
    if nombre == "original":
        if config.ARCHIVO_ACTUAL.exists():
            config.HISTORIAL.mkdir(exist_ok=True)
            shutil.copy2(config.ARCHIVO_ACTUAL, config.HISTORIAL / f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv")
            config.ARCHIVO_ACTUAL.unlink()
        return "original"
    versiones = listar_versiones()
    if not versiones:
        raise ErrorIngesta("No hay versiones anteriores guardadas")
    elegida = nombre or versiones[-1]
    if elegida not in versiones:
        raise ErrorIngesta(f"No existe la version {elegida}. Disponibles: {', '.join(versiones)}")
    origen = config.HISTORIAL / elegida
    if config.ARCHIVO_ACTUAL.exists():
        shutil.copy2(config.ARCHIVO_ACTUAL, config.HISTORIAL / f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv")
    shutil.copy2(origen, config.ARCHIVO_ACTUAL)
    return elegida


def agregar_baja(telefono, motivo="solicitud de la persona"):
    """Agrega un telefono a la lista de quienes no deben recibir mensajes. Devuelve False si ya estaba."""
    clave = clave_telefono(telefono)
    if len(clave) < 8:
        raise ErrorIngesta("Telefono no valido: debe tener al menos 8 digitos")
    existentes = {clave_telefono(t) for t in leer_bajas(config.ARCHIVO_BAJAS)}
    if clave in existentes:
        return False
    config.DATOS.mkdir(exist_ok=True)
    nuevo = not config.ARCHIVO_BAJAS.exists()
    fila = pd.DataFrame([{"telefono": telefono, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "motivo": motivo}])
    fila.to_csv(config.ARCHIVO_BAJAS, mode="a", header=nuevo, index=False, encoding="utf-8")
    return True
