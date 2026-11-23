"""Lectura, limpieza y enriquecimiento de la base de leads.

Tres pasos, cada uno una funcion:
    parsear(df_texto)       convierte texto a tipos (fechas, numeros) y renombra `estado` a `entidad`
    enriquecer(df, bajas)   ordena y agrega las banderas por telefono (duplicado, cliente, rechazo,
                            seguimiento, baja) y los intentos previos
    cargar_leads(ruta)      lee un CSV y aplica los dos pasos anteriores

Donde cambiar cosas
    - Formatos de fecha aceptados: `_FORMATOS_FECHA`.
    - Rango de edad valido: `enriquecer`.
    - Como se identifica a una misma persona: `clave_telefono` (ultimos 10 digitos).
"""

import re
from datetime import datetime

import pandas as pd

_FORMATOS_FECHA = ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M")


def clave_telefono(valor):
    """Identifica a una persona por los ultimos 10 digitos de su telefono."""
    digitos = re.sub(r"\D", "", "" if valor is None or valor != valor else str(valor))
    return digitos[-10:]


def _parsear_fecha(valor):
    if valor is None:
        return pd.NaT
    texto = str(valor).strip()
    if texto == "":
        return pd.NaT
    for formato in _FORMATOS_FECHA:
        try:
            return pd.Timestamp(datetime.strptime(texto, formato))
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha no reconocido: {valor!r}")


def parsear(df_texto):
    df = df_texto.rename(columns={"estado": "entidad"}).copy()
    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"].map(_parsear_fecha))
    df["primer_contacto"] = pd.to_datetime(df["primer_contacto"].map(_parsear_fecha))
    edad = pd.to_numeric(df["edad"], errors="coerce")
    df["edad"] = edad.where(edad.between(18, 100))
    df["plan_de_interes"] = pd.to_numeric(df["plan_de_interes"], errors="coerce")
    df["monto_venta"] = pd.to_numeric(df["monto_venta"], errors="coerce")
    for columna in ("asesor", "anuncio"):
        df[columna] = df[columna].replace("", pd.NA)
    return df


def _verdadero(serie):
    return serie.astype(str).str.strip().str.lower().isin({"1", "true", "si", "sí", "yes", "s", "x"})


def enriquecer(df, bajas=None):
    df = df.copy()
    df["edad_valida"] = df["edad"].between(18, 100)
    df = df.sort_values(["fecha_registro", "lead_id"]).reset_index(drop=True)
    df["telefono_clave"] = df["telefono"].map(clave_telefono)

    df["es_duplicado"] = df.duplicated("telefono_clave", keep="first")
    por_telefono = df.groupby("telefono_clave")["resultado"]
    df["ya_es_cliente"] = por_telefono.transform(lambda s: s.eq("venta").any())
    df["telefono_rechazo"] = por_telefono.transform(lambda s: s.eq("no_interesado").any())
    df["telefono_en_seguimiento"] = por_telefono.transform(lambda s: s.eq("en_seguimiento").any())

    claves_baja = {clave_telefono(t) for t in (bajas or [])}
    en_baja = df["telefono_clave"].isin(claves_baja)
    if "baja" in df.columns:
        marcada = df.groupby("telefono_clave")["baja"].transform(lambda s: _verdadero(s).any())
        en_baja = en_baja | marcada
    df["en_lista_bajas"] = en_baja

    contactos = df.groupby("telefono_clave")["primer_contacto"]
    df["intentos_previos"] = contactos.transform(lambda s: s.notna().sum()).astype(int)
    df["ultimo_contacto"] = contactos.transform("max")
    return df


def leer_bajas(ruta):
    """Lee la lista de telefonos que pidieron no recibir mensajes (columna `telefono`)."""
    if ruta is None or not ruta.exists():
        return []
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig")["telefono"].tolist()


def cargar_leads(ruta, bajas=None):
    crudo = pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return enriquecer(parsear(crudo), bajas)


def fecha_sugerida(df):
    """Dia siguiente al ultimo registro, a las 08:00: el 'hoy' natural de una lista nueva."""
    ultimo = df["fecha_registro"].max()
    return (ultimo.normalize() + pd.Timedelta(days=1)).to_pydatetime().replace(hour=8)
