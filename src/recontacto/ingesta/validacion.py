"""Validacion: renombra sinonimos de columnas y revisa fila por fila (lo rechazado queda con su motivo)."""

import re

import pandas as pd

from .esquema import CANALES_CONOCIDOS, COLUMNAS, OPCIONALES, REQUERIDAS, SINONIMOS, ErrorIngesta
from .utilidades import _clave_columna, _fecha, _numero, _resultado, _texto


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
