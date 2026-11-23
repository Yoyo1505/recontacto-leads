from datetime import timedelta

import numpy as np
import pandas as pd

from .config import REGLAS

MOTIVOS = {
    "baja": "Pidio no recibir mas mensajes",
    "duplicado": "Registro repetido de otro lead con el mismo telefono",
    "cliente": "Ya es cliente",
    "rechazo": "Dijo que no le interesa",
    "en_seguimiento": "Ya esta en conversacion con un asesor",
    "fuera_ventana": "Fuera de la ventana de recuperacion",
    "max_intentos": "Alcanzo el maximo de intentos",
}


def es_horario_valido(momento, reglas=REGLAS):
    return momento.weekday() in reglas.dias_permitidos and momento.hour in reglas.horas_permitidas


def horarios_validos(ahora, reglas=REGLAS):
    primer_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    horarios = []
    for dia in range(reglas.horizonte_dias + 1):
        fecha = primer_dia + timedelta(days=dia)
        for hora in reglas.horas_permitidas:
            momento = fecha.replace(hour=hora)
            if momento > ahora and es_horario_valido(momento, reglas):
                horarios.append(momento)
    return horarios


def evaluar_elegibilidad(df, ahora, reglas=REGLAS):
    dias = (pd.Timestamp(ahora) - df["fecha_registro"]).dt.total_seconds() / 86400
    condiciones = [
        df["en_lista_bajas"],
        df["es_duplicado"],
        df["ya_es_cliente"],
        df["telefono_rechazo"],
        df["telefono_en_seguimiento"],
        dias > reglas.ventana_dias,
        df["intentos_previos"] >= reglas.max_intentos,
    ]
    claves = list(MOTIVOS)
    resultado = df.copy()
    resultado["dias_desde_registro"] = dias
    resultado["motivo_exclusion"] = np.select(condiciones, claves, default="")
    resultado["motivo_exclusion"] = resultado["motivo_exclusion"].replace("", pd.NA)
    return resultado


def primer_horario_permitido(ultimo_contacto, ahora, reglas=REGLAS):
    if pd.isna(ultimo_contacto):
        return pd.Timestamp(ahora)
    return max(pd.Timestamp(ahora), ultimo_contacto + timedelta(hours=reglas.horas_entre_intentos))
