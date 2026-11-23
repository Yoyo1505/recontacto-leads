import numpy as np
import pandas as pd

from . import config

CATEGORICAS = ["canal", "objetivo", "franja_hora", "rango_espera", "dia_semana"]
NUMERICAS = ["edad", "plan_de_interes"]
COLUMNAS = CATEGORICAS + NUMERICAS

_FRANJAS = ["<9", "9-10", "11-12", "13-15", "16-18", "19+"]
_ESPERAS = ["<30min", "30min-2h", "2-6h", "6-12h", "12-24h", ">24h"]


def franja_hora(horas):
    serie = pd.cut(pd.Series(horas), [-1, 8, 10, 12, 15, 18, 24], labels=_FRANJAS)
    return serie.astype(str).to_numpy()


def rango_espera(horas_espera):
    cortes = [-np.inf, 0.5, 2, 6, 12, 24, np.inf]
    serie = pd.cut(pd.Series(horas_espera, dtype=float), cortes, labels=_ESPERAS)
    return serie.astype(str).to_numpy()


def desde_contactos(df):
    contactados = df[df["primer_contacto"].notna() & ~df["es_duplicado"]].copy()
    espera = (contactados["primer_contacto"] - contactados["fecha_registro"]).dt.total_seconds() / 3600
    contactados["espera_h"] = espera
    contactados["franja_hora"] = franja_hora(contactados["primer_contacto"].dt.hour)
    contactados["rango_espera"] = rango_espera(espera)
    contactados["dia_semana"] = contactados["primer_contacto"].dt.weekday.map(
        lambda d: config.DIAS_SEMANA[d]
    )
    y = (contactados["resultado"] != "no_contesta").astype(int)
    return contactados[COLUMNAS + ["fecha_registro"]], y


def marco_horarios(leads, horarios):
    base = leads[["canal", "objetivo", "edad", "plan_de_interes"]].reset_index(names="indice_lead")
    slots = pd.DataFrame({"horario": pd.to_datetime(list(horarios))})
    cruce = base.merge(slots, how="cross")
    cruce["franja_hora"] = franja_hora(cruce["horario"].dt.hour)
    cruce["dia_semana"] = cruce["horario"].dt.weekday.map(lambda d: config.DIAS_SEMANA[d])
    cruce["rango_espera"] = rango_espera(np.full(len(cruce), config.ESPERA_REFERENCIA_H))
    return cruce
