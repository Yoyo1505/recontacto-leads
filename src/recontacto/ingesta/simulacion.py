"""Que haria la herramienta con las personas que llegan en un archivo, sin guardar nada."""

import pandas as pd

from .. import config
from ..data import enriquecer, leer_bajas


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
    from .. import features, pipeline
    from ..data import fecha_sugerida
    from ..model import ModeloContacto

    reglas = reglas or config.REGLAS
    df = enriquecer(informe.fusionado.copy(), leer_bajas(config.ARCHIVO_BAJAS))
    ahora = hoy or fecha_sugerida(df)
    X, y = features.desde_contactos(df)
    modelo = ModeloContacto("logistica").entrenar(X, y)
    lista, excluidos = pipeline.generar_lista(df, modelo, ahora, reglas)
    return decisiones_para(list(informe.agregados) + list(informe.actualizados), lista, excluidos)
