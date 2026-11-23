"""Ingesta de datos: leer, validar, fusionar y versionar la base de leads.

Flujo (cada paso es una funcion)
    leer_fuente / leer_bytes   CSV, JSON, Excel, Parquet, SQLite, bases SQL (SQLAlchemy) y URLs
                               (http, https, s3, gs, az) -> tabla cruda
    normalizar_columnas        acepta sinonimos de columnas y avisa de las que faltan o sobran
    validar                    revisa fila por fila; lo rechazado queda con su motivo, nada se pierde
    fusionar                   agrega leads nuevos y actualiza los existentes por `lead_id`; nunca borra
    guardar_version            guarda la base nueva y una copia de la anterior (se puede restaurar)

Cuidado con las personas
    - Un archivo mal formado no cambia nada: primero se muestra el informe y solo se aplica si se pide.
    - Los telefonos que pidieron no recibir mensajes se guardan en `data/bajas.csv` (`agregar_baja`) y
      se respetan siempre, venga el dato de donde venga.
    - Las contrasenas de las cadenas de conexion no se escriben en pantalla, bitacoras ni archivos.

Donde cambiar cosas
    - Columnas obligatorias y sinonimos: `REQUERIDAS` y `SINONIMOS`.
    - Valores validos de `resultado`: `RESULTADOS` y `SINONIMOS_RESULTADO`.
    - Reglas de validacion por fila: funcion `validar`.
    - Cuantas versiones se conservan: `config.VERSIONES_A_CONSERVAR`.

Uso desde la linea de comandos
    python -m recontacto.ingesta --origen nuevos.xlsx                 informe (no cambia nada)
    python -m recontacto.ingesta --origen nuevos.xlsx --simular        que pasaria con esas personas
    python -m recontacto.ingesta --origen nuevos.xlsx --aplicar        guarda los cambios
    python -m recontacto.ingesta --origen env:RECONTACTO_DB_URL --tabla leads --aplicar
    python -m recontacto.ingesta --listar-versiones | --restaurar [nombre|original]
    python -m recontacto.ingesta --agregar-baja 5512345678
"""

import argparse
import json
import os
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from . import config
from .data import clave_telefono, enriquecer, leer_bajas, parsear

COLUMNAS = [
    "lead_id",
    "fecha_registro",
    "canal",
    "anuncio",
    "estado",
    "edad",
    "objetivo",
    "plan_de_interes",
    "telefono",
    "asesor",
    "primer_contacto",
    "resultado",
    "monto_venta",
]
REQUERIDAS = ("lead_id", "fecha_registro", "canal", "telefono", "resultado")
OPCIONALES = ("baja", "variante")
RESULTADOS = ("no_contesta", "sin_contactar", "en_seguimiento", "no_interesado", "venta")
SINONIMOS = {
    "lead_id": {"id", "id_lead", "lead", "folio", "leadid"},
    "fecha_registro": {"fecha", "fecha_de_registro", "fecha_alta", "created_at", "registro"},
    "canal": {"fuente", "origen", "source", "channel"},
    "anuncio": {"ad", "creativo"},
    "estado": {"entidad", "estado_republica", "entidad_federativa", "state"},
    "edad": {"age"},
    "objetivo": {"motivo_de_consulta", "goal"},
    "plan_de_interes": {"plan", "plan_interes"},
    "telefono": {"celular", "whatsapp", "tel", "phone", "telefono_celular"},
    "asesor": {"agente", "advisor", "asignado"},
    "primer_contacto": {"fecha_primer_contacto", "contacted_at", "primer_contacto_fecha"},
    "resultado": {"status", "resultado_final", "etapa"},
    "monto_venta": {"monto", "importe", "monto_de_venta"},
    "baja": {"no_contactar", "opt_out", "unsubscribe"},
    "variante": {"variante_mensaje", "mensaje_variante"},
}
SINONIMOS_RESULTADO = {"contesto": "en_seguimiento", "no_contestó": "no_contesta", "nuevo": "sin_contactar"}
CANALES_CONOCIDOS = {"meta": "Meta", "tiktok": "TikTok", "google": "Google", "referido": "Referido", "organico": "Organico"}
FORMATOS_FECHA = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
)
SEGUIMIENTO = ("resultado", "primer_contacto", "asesor", "monto_venta", "plan_de_interes", "edad", "objetivo", "anuncio", "entidad", "canal", "variante")
ESQUEMAS_BASE_DE_DATOS = {"sqlite", "postgresql", "postgres", "mysql", "mariadb", "mssql", "oracle"}
SQL_PROHIBIDO = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|attach|pragma|exec|replace)\b", re.I)
LIMITE_BYTES = 200 * 1024 * 1024


class ErrorIngesta(Exception):
    """Problema que impide leer o procesar la fuente; el mensaje dice como resolverlo."""


@dataclass
class Informe:
    origen: str = ""
    filas_leidas: int = 0
    columnas_mapeadas: dict = field(default_factory=dict)
    columnas_ignoradas: list = field(default_factory=list)
    validos: int = 0
    rechazados: pd.DataFrame = field(default_factory=pd.DataFrame)
    advertencias: list = field(default_factory=list)
    agregados: list = field(default_factory=list)
    actualizados: dict = field(default_factory=dict)
    sin_cambio: int = 0
    conflictos: list = field(default_factory=list)
    fusionado: pd.DataFrame = None
    version_guardada: str = None
    aplicado: bool = False

    @property
    def hay_cambios(self):
        return bool(self.agregados or self.actualizados)

    def texto(self):
        lineas = [
            f"Origen: {self.origen}",
            f"Filas leidas: {self.filas_leidas}",
            f"Validas: {self.validos} | Rechazadas: {len(self.rechazados)} | Advertencias: {len(self.advertencias)}",
            f"Nuevas: {len(self.agregados)} | Actualizadas: {len(self.actualizados)} | Sin cambio: {self.sin_cambio} | Conflictos: {len(self.conflictos)}",
        ]
        if self.columnas_ignoradas:
            lineas.append("Columnas ignoradas: " + ", ".join(map(str, self.columnas_ignoradas)))
        if len(self.rechazados):
            lineas.append("Motivos de rechazo:")
            conteo = self.rechazados["motivo"].str.replace(r":.*$", "", regex=True).value_counts()
            lineas.extend(f"  {n} x {m}" for m, n in conteo.items())
        for lead, mensaje in self.advertencias[:10]:
            lineas.append(f"  Aviso {lead}: {mensaje}")
        if len(self.advertencias) > 10:
            lineas.append(f"  ... y {len(self.advertencias) - 10} avisos mas")
        if self.aplicado:
            lineas.append(f"Cambios guardados. Copia de la version anterior: {self.version_guardada or 'no hacia falta (base original intacta)'}")
        else:
            lineas.append("No se guardo nada (usa --aplicar para guardar).")
        return "\n".join(lineas)


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


def normalizar_columnas(df):
    """Renombra sinonimos a las columnas canonicas. Devuelve (tabla de texto, mapeo, ignoradas)."""
    por_clave = {}
    for columna in df.columns:
        por_clave.setdefault(_clave_columna(columna), columna)
    mapeo = {}
    for canonica in COLUMNAS + list(OPCIONALES):
        for candidata in [canonica, *sorted(SINONIMOS.get(canonica, ()))]:
            if candidata in por_clave and canonica not in mapeo:
                mapeo[canonica] = por_clave[candidata]
    faltantes = [c for c in REQUERIDAS if c not in mapeo]
    if faltantes:
        raise ErrorIngesta(
            "Faltan columnas obligatorias: " + ", ".join(faltantes) + ". Columnas encontradas: " + ", ".join(map(str, df.columns))
        )
    texto = pd.DataFrame(index=df.index)
    for canonica in COLUMNAS + [o for o in OPCIONALES if o in mapeo]:
        texto[canonica] = df[mapeo[canonica]].map(_texto) if canonica in mapeo else ""
    usadas = set(mapeo.values())
    ignoradas = [c for c in df.columns if c not in usadas]
    return texto, {k: str(v) for k, v in mapeo.items() if k != v}, ignoradas


def validar(texto):
    """Revisa fila por fila. Devuelve (leads tipados, rechazados con motivo, advertencias)."""
    filas, rechazos, avisos, vistos = [], [], [], set()
    for indice, fila in texto.iterrows():
        lead = fila["lead_id"]

        def rechazar(motivo):
            rechazos.append({**fila.to_dict(), "motivo": motivo})

        if lead == "":
            rechazar("lead_id vacio")
            continue
        if lead in vistos:
            rechazar("lead_id repetido en el archivo")
            continue
        registro = _fecha(fila["fecha_registro"])
        if registro is None:
            rechazar(f"fecha_registro no valida: {fila['fecha_registro']!r}")
            continue
        if fila["canal"] == "":
            rechazar("canal vacio")
            continue
        if len(re.sub(r"\D", "", fila["telefono"])) < 8:
            rechazar(f"telefono no valido: {fila['telefono']!r}")
            continue
        resultado = _resultado(fila["resultado"])
        if resultado is None:
            rechazar(f"resultado desconocido: {fila['resultado']!r}")
            continue
        contacto = None
        if fila["primer_contacto"] != "":
            contacto = _fecha(fila["primer_contacto"])
            if contacto is None:
                rechazar(f"primer_contacto no valido: {fila['primer_contacto']!r}")
                continue

        edad = _numero(fila["edad"])
        if fila["edad"] != "" and (edad is None or not 18 <= edad <= 100):
            avisos.append((lead, f"edad fuera de rango o no numerica ({fila['edad']!r}); se deja vacia"))
            edad = None
        monto = _numero(fila["monto_venta"])
        if fila["monto_venta"] != "" and (monto is None or monto < 0):
            avisos.append((lead, f"monto_venta no valido ({fila['monto_venta']!r}); se deja vacio"))
            monto = None
        if resultado == "venta" and not monto:
            avisos.append((lead, "venta sin monto"))
        if contacto is not None and contacto < registro:
            avisos.append((lead, "primer_contacto anterior al registro"))
        if resultado == "sin_contactar" and contacto is not None:
            avisos.append((lead, "marcado sin_contactar pero trae primer_contacto"))
        if resultado == "no_contesta" and contacto is None:
            avisos.append((lead, "marcado no_contesta pero sin primer_contacto"))

        canal = CANALES_CONOCIDOS.get(_clave_columna(fila["canal"]), fila["canal"])
        registro_valido = {
            "lead_id": lead,
            "fecha_registro": registro,
            "canal": canal,
            "anuncio": fila["anuncio"],
            "entidad": fila["estado"],
            "edad": edad,
            "objetivo": fila["objetivo"],
            "plan_de_interes": _numero(fila["plan_de_interes"]),
            "telefono": fila["telefono"],
            "asesor": fila["asesor"],
            "primer_contacto": contacto,
            "resultado": resultado,
            "monto_venta": monto,
        }
        for opcional in OPCIONALES:
            if opcional in texto.columns:
                registro_valido[opcional] = fila[opcional]
        filas.append(registro_valido)
        vistos.add(lead)
    columnas = [c if c != "estado" else "entidad" for c in COLUMNAS] + [o for o in OPCIONALES if o in texto.columns]
    validos = pd.DataFrame(filas, columns=columnas)
    validos["fecha_registro"] = pd.to_datetime(validos["fecha_registro"])
    validos["primer_contacto"] = pd.to_datetime(validos["primer_contacto"])
    return validos, pd.DataFrame(rechazos), avisos


def leer_canonico(ruta=None):
    ruta = ruta or config.ruta_datos_activa()
    return parsear(pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig"))


def fusionar(actual, nuevo):
    """Agrega los leads nuevos y actualiza los que ya existen. Nunca borra. Devuelve (tabla, resumen)."""
    resumen = {"agregados": [], "actualizados": {}, "sin_cambio": 0, "conflictos": []}
    columnas = list(actual.columns) + [c for c in nuevo.columns if c not in actual.columns]
    base = actual.reindex(columns=columnas).set_index("lead_id")
    existentes = base.to_dict("index")
    nuevas_filas = []
    for _, fila in nuevo.reindex(columns=columnas).iterrows():
        lead = fila["lead_id"]
        if lead not in existentes:
            nuevas_filas.append(fila.to_dict())
            resumen["agregados"].append(lead)
            continue
        previa = existentes[lead]
        if clave_telefono(previa["telefono"]) != clave_telefono(fila["telefono"]):
            resumen["conflictos"].append(lead)
            continue
        campos = [c for c in SEGUIMIENTO if c in columnas and not _igual(previa.get(c), fila.get(c))]
        if campos:
            for campo in campos:
                base.at[lead, campo] = fila[campo]
            resumen["actualizados"][lead] = campos
        else:
            resumen["sin_cambio"] += 1
    fusionado = base.reset_index()
    if nuevas_filas:
        fusionado = pd.concat([fusionado, pd.DataFrame(nuevas_filas, columns=columnas)], ignore_index=True)
    fusionado = fusionado[columnas]
    for columna in ("edad", "plan_de_interes", "monto_venta"):
        fusionado[columna] = pd.to_numeric(fusionado[columna], errors="coerce")
    for columna in ("fecha_registro", "primer_contacto"):
        fusionado[columna] = pd.to_datetime(fusionado[columna])
    return fusionado, resumen


def procesar(crudo, origen="", base=None):
    """Normaliza, valida y fusiona sin guardar nada. Devuelve un `Informe`."""
    informe = Informe(origen=origen, filas_leidas=len(crudo))
    texto, mapeo, ignoradas = normalizar_columnas(crudo)
    informe.columnas_mapeadas, informe.columnas_ignoradas = mapeo, ignoradas
    validos, rechazados, avisos = validar(texto)
    informe.validos, informe.rechazados, informe.advertencias = len(validos), rechazados, avisos
    actual = base if base is not None else leer_canonico()
    fusionado, resumen = fusionar(actual, validos)
    informe.fusionado = fusionado
    informe.agregados, informe.actualizados = resumen["agregados"], resumen["actualizados"]
    informe.sin_cambio, informe.conflictos = resumen["sin_cambio"], resumen["conflictos"]
    if informe.conflictos:
        extra = pd.DataFrame([{"lead_id": c, "motivo": "lead_id ya existe con otro telefono"} for c in informe.conflictos])
        informe.rechazados = pd.concat([informe.rechazados, extra], ignore_index=True)
    return informe


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


def decisiones_para(ids, lista, excluidos):
    """Para cada lead de `ids`: su horario y mensaje, o el motivo por el que hoy no se le contactaria."""
    filas = []
    for lead in ids:
        en_lista = lista[lista["lead_id"] == lead]
        if len(en_lista):
            f = en_lista.iloc[0]
            filas.append(
                {"lead_id": lead, "decision": f["accion"], "horario": f["horario_asignado"], "motivo": f["motivo"], "mensaje": f["mensaje"], "prioridad": f["prioridad"]}
            )
            continue
        fuera = excluidos[excluidos["lead_id"] == lead]
        razon = fuera.iloc[0]["motivo"] if len(fuera) else "No requiere recontacto"
        filas.append({"lead_id": lead, "decision": "no contactar", "horario": pd.NaT, "motivo": razon, "mensaje": "", "prioridad": None})
    return pd.DataFrame(filas, columns=["lead_id", "decision", "horario", "motivo", "mensaje", "prioridad"])


def simular_llegada(informe, hoy=None, reglas=None):
    """Que haria la herramienta con los leads nuevos o actualizados, sin guardar nada."""
    from . import features, pipeline
    from .data import fecha_sugerida
    from .model import ModeloContacto

    reglas = reglas or config.REGLAS
    df = enriquecer(informe.fusionado.copy(), leer_bajas(config.ARCHIVO_BAJAS))
    ahora = hoy or fecha_sugerida(df)
    X, y = features.desde_contactos(df)
    modelo = ModeloContacto("logistica").entrenar(X, y)
    lista, excluidos = pipeline.generar_lista(df, modelo, ahora, reglas)
    return decisiones_para(list(informe.agregados) + list(informe.actualizados), lista, excluidos)


def _parser():
    p = argparse.ArgumentParser(description="Actualiza la base de leads desde un archivo, una base de datos o la nube")
    p.add_argument("--origen", help="ruta, URL, cadena de conexion o env:NOMBRE_DE_VARIABLE")
    p.add_argument("--tabla")
    p.add_argument("--consulta", help="SELECT de solo lectura")
    p.add_argument("--hoja", help="hoja de Excel")
    p.add_argument("--aplicar", action="store_true", help="guarda los cambios (sin esto solo se muestra el informe)")
    p.add_argument("--simular", action="store_true", help="muestra que haria la herramienta con las personas nuevas")
    p.add_argument("--listar-versiones", action="store_true")
    p.add_argument("--restaurar", nargs="?", const="ultima", metavar="VERSION")
    p.add_argument("--agregar-baja", metavar="TELEFONO")
    return p


def main(argumentos=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argumentos)
    try:
        if args.listar_versiones:
            versiones = listar_versiones()
            print("\n".join(versiones) if versiones else "No hay versiones guardadas.")
            return 0
        if args.restaurar:
            elegida = restaurar(None if args.restaurar == "ultima" else args.restaurar)
            print(f"Base restaurada a: {elegida}")
            return 0
        if args.agregar_baja:
            print("Telefono agregado a la lista de bajas." if agregar_baja(args.agregar_baja) else "Ese telefono ya estaba en la lista de bajas.")
            return 0
        if not args.origen:
            print("Indica --origen, --listar-versiones, --restaurar o --agregar-baja.")
            return 2
        crudo, descripcion = leer_fuente(args.origen, args.tabla, args.consulta, args.hoja)
        informe = procesar(crudo, descripcion)
        if args.aplicar:
            aplicar(informe)
        print(informe.texto())
        if args.simular:
            pd.set_option("display.width", 220, "display.max_colwidth", 120)
            print("\nQue haria la herramienta con estas personas:")
            print(simular_llegada(informe).to_string(index=False))
        return 0
    except ErrorIngesta as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
