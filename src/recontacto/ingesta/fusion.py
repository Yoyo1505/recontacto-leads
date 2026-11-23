"""Fusion: agrega los leads nuevos y actualiza los existentes por `lead_id`. Nunca borra."""

import pandas as pd

from .. import config
from ..data import clave_telefono, parsear
from .esquema import SEGUIMIENTO, Informe
from .utilidades import _igual
from .validacion import normalizar_columnas, validar


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
