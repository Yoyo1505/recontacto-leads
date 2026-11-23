"""Lectura de fuentes: archivos (CSV, JSON, Excel, Parquet), SQLite, bases SQL, URLs y nube.

Las bases SQL se leen en solo lectura (un SELECT sin instrucciones que modifiquen datos) y las contrasenas
de las cadenas de conexion nunca se muestran.
"""

import json
import os
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .esquema import ESQUEMAS_BASE_DE_DATOS, LIMITE_BYTES, SQL_PROHIBIDO, ErrorIngesta
from .utilidades import _extension, enmascarar


def leer_bytes(nombre, datos, hoja=None):
    """Convierte el contenido de un archivo (CSV, JSON, Excel o Parquet) en una tabla cruda."""
    if len(datos) > LIMITE_BYTES:
        raise ErrorIngesta("El archivo supera 200 MB")
    ext = _extension(nombre)
    flujo = BytesIO(datos)
    try:
        if ext in (".csv", ".txt", ".tsv"):
            return pd.read_csv(flujo, dtype=str, keep_default_na=False, sep=None, engine="python", encoding="utf-8-sig")
        if ext in (".json", ".jsonl", ".ndjson"):
            texto = datos.decode("utf-8-sig")
            if ext in (".jsonl", ".ndjson"):
                return pd.DataFrame([json.loads(linea) for linea in texto.splitlines() if linea.strip()])
            objeto = json.loads(texto)
            if isinstance(objeto, dict):
                listas = [v for v in objeto.values() if isinstance(v, list)]
                if not listas:
                    raise ErrorIngesta("El JSON debe ser una lista de registros o un objeto que contenga una lista")
                objeto = listas[0]
            return pd.DataFrame(objeto)
        if ext in (".xlsx", ".xlsm", ".xls"):
            return pd.read_excel(flujo, sheet_name=hoja if hoja else 0, dtype=object)
        if ext == ".parquet":
            return pd.read_parquet(flujo)
    except ErrorIngesta:
        raise
    except ImportError as error:
        raise ErrorIngesta(f"Falta una libreria para leer {ext}: {error}") from error
    except Exception as error:
        raise ErrorIngesta(f"No se pudo leer {nombre} como {ext}: {error}") from error
    raise ErrorIngesta(f"Formato no soportado: {ext or 'sin extension'}. Usa csv, json, jsonl, xlsx, parquet, sqlite o una base SQL")


def _leer_base_de_datos(cadena, tabla, consulta):
    try:
        from sqlalchemy import create_engine, text
    except ImportError as error:
        raise ErrorIngesta("Para leer de una base de datos instala sqlalchemy: pip install sqlalchemy") from error
    if cadena.startswith("postgres://"):
        cadena = "postgresql://" + cadena[len("postgres://"):]
    if consulta:
        sentencia = consulta.strip().rstrip(";")
        if not re.match(r"^(select|with)\b", sentencia, re.I) or ";" in sentencia or SQL_PROHIBIDO.search(sentencia):
            raise ErrorIngesta("La consulta debe ser de solo lectura (un SELECT, sin ';' ni instrucciones que modifiquen datos)")
    elif tabla:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", tabla):
            raise ErrorIngesta("Nombre de tabla no valido")
        sentencia = f"SELECT * FROM {tabla}"
    else:
        raise ErrorIngesta("Indica la tabla (--tabla) o una consulta de lectura (--consulta)")
    try:
        motor = create_engine(cadena)
        with motor.connect() as conexion:
            return pd.read_sql_query(text(sentencia), conexion)
    except ImportError as error:
        raise ErrorIngesta(f"Falta el conector de la base de datos ({error}). Ejemplos: pip install psycopg2-binary, pip install pymysql") from error
    except Exception as error:
        raise ErrorIngesta(f"No se pudo leer de la base de datos: {enmascarar(error)}") from None


def leer_fuente(origen, tabla=None, consulta=None, hoja=None):
    """Lee una fuente y devuelve (tabla cruda, descripcion sin secretos).

    `origen` puede ser: una ruta local, una URL (http, https, s3, gs, az), una cadena de conexion
    SQL, o `env:NOMBRE` para tomar cualquiera de las anteriores de una variable de entorno.
    """
    if origen.startswith("env:"):
        nombre = origen[4:]
        origen = os.environ.get(nombre, "")
        if not origen:
            raise ErrorIngesta(f"La variable de entorno {nombre} no esta definida")
    descripcion = enmascarar(origen)
    esquema = urlparse(origen).scheme.split("+")[0].lower() if "://" in origen else ""
    if esquema in ESQUEMAS_BASE_DE_DATOS:
        return _leer_base_de_datos(origen, tabla, consulta), descripcion
    if _extension(origen) in (".db", ".sqlite", ".sqlite3") and "://" not in origen:
        ruta = Path(origen)
        if not ruta.exists():
            raise ErrorIngesta(f"No existe el archivo {ruta}")
        return _leer_base_de_datos(f"sqlite:///{ruta.resolve().as_posix()}", tabla or "leads", consulta), descripcion
    if esquema in ("http", "https"):
        import requests

        try:
            respuesta = requests.get(origen, timeout=30)
            respuesta.raise_for_status()
        except requests.RequestException as error:
            raise ErrorIngesta(f"No se pudo descargar {descripcion}: {enmascarar(error)}") from None
        return leer_bytes(origen, respuesta.content, hoja), descripcion
    if "://" in origen:
        try:
            import fsspec

            with fsspec.open(origen, "rb") as archivo:
                datos = archivo.read()
        except ImportError as error:
            raise ErrorIngesta(
                "Falta la libreria de ese servicio en la nube: s3 -> pip install s3fs; gs -> pip install gcsfs; az -> pip install adlfs. "
                "Las credenciales van en variables de entorno, nunca en el comando."
            ) from error
        except Exception as error:
            raise ErrorIngesta(f"No se pudo descargar {descripcion}: {enmascarar(error)}") from None
        return leer_bytes(origen, datos, hoja), descripcion
    ruta = Path(origen)
    if not ruta.exists():
        raise ErrorIngesta(f"No existe el archivo {ruta}")
    return leer_bytes(ruta.name, ruta.read_bytes(), hoja), descripcion
