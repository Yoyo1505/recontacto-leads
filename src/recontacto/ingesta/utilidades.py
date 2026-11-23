"""Funciones pequenas compartidas: ocultar secretos y convertir textos, fechas y numeros."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .esquema import FORMATOS_FECHA, RESULTADOS, SINONIMOS_RESULTADO


def enmascarar(texto):
    """Oculta contrasenas y llaves de una cadena de conexion o URL antes de mostrarla."""
    texto = re.sub(r"(://[^:/@\s]+:)[^@\s]+@", r"\1***@", str(texto))
    return re.sub(r"([?&](?:token|key|sig|password|pwd|secret|access_key)=)[^&\s]+", r"\1***", texto, flags=re.I)


def _clave_columna(nombre):
    sin_acentos = unicodedata.normalize("NFD", str(nombre))
    sin_acentos = "".join(c for c in sin_acentos if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", sin_acentos.strip().lower()).strip("_")


def _texto(valor):
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else str(valor)
    if isinstance(valor, (pd.Timestamp, datetime)):
        return pd.Timestamp(valor).strftime("%Y-%m-%d %H:%M")
    return str(valor).strip()


def _fecha(texto):
    texto = texto.strip()
    for formato in FORMATOS_FECHA:
        try:
            return pd.Timestamp(datetime.strptime(texto, formato)).floor("min")
        except ValueError:
            continue
    return None


def _numero(texto):
    if texto == "":
        return None
    try:
        return float(texto.replace(",", ""))
    except ValueError:
        return None


def _resultado(texto):
    clave = _clave_columna(texto)
    clave = SINONIMOS_RESULTADO.get(clave, clave)
    return clave if clave in RESULTADOS else None


def _igual(a, b):
    vacio_a = a is None or a == "" or (not isinstance(a, str) and pd.isna(a))
    vacio_b = b is None or b == "" or (not isinstance(b, str) and pd.isna(b))
    if vacio_a or vacio_b:
        return vacio_a and vacio_b
    return a == b


def _extension(nombre):
    return Path(urlparse(str(nombre)).path).suffix.lower()
