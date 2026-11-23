import pandas as pd

from . import config, features, mensajes, policy
from .config import REGLAS

_ETIQUETAS = {
    "canal": "canal {}",
    "objetivo": "perfil {}",
    "franja_hora": "horario {}",
    "dia_semana": "día {}",
    "edad": "edad {:.0f}",
}
_VISIBLES = tuple(_ETIQUETAS)
_UMBRAL = 0.03

COLUMNAS_LISTA = [
    "prioridad",
    "lead_id",
    "canal",
    "accion",
    "intento",
    "nunca_contactado",
    "dias_desde_registro",
    "horario_asignado",
    "prob_asignada",
    "prob_promedio",
    "motivo",
    "mensaje",
    "origen_mensaje",
    "etapa",
    "variante",
    "asesor",
    "telefono",
]


def _etiqueta(columna, valor):
    return _ETIQUETAS[columna].format(valor)


def _explicar(fila, aporte, nunca_contactado):
    if nunca_contactado:
        return "Nunca fue contactado: se agenda en la primera hora hábil con espacio, sin esperar un mejor horario."
    visibles = {c: aporte[c] for c in _VISIBLES if not pd.isna(fila[c])}
    ordenados = sorted(visibles.items(), key=lambda par: par[1], reverse=True)
    a_favor = [c for c, v in ordenados if v > _UMBRAL][:2]
    en_contra = [c for c, v in reversed(ordenados) if v < -_UMBRAL][:1]
    dia = config.DIAS_SEMANA[fila["horario"].weekday()]
    partes = [
        f"Horario asignado: {dia} {fila['horario'].hour:02d}:00 "
        f"({fila['prob']:.0%} de probabilidad de contestar contra {fila['prob_promedio']:.0%} en promedio)."
    ]
    if a_favor:
        partes.append("A favor: " + ", ".join(_etiqueta(c, fila[c]) for c in a_favor) + ".")
    if en_contra:
        partes.append("En contra: " + ", ".join(_etiqueta(c, fila[c]) for c in en_contra) + ".")
    return " ".join(partes)


def _franja_texto(horario, ahora):
    parte = "por la mañana" if horario.hour < 12 else "por la tarde"
    if horario.date() == ahora.date():
        return f"hoy {parte}"
    return f"el {config.DIAS_SEMANA[horario.weekday()]} {parte}"


def _probabilidades_por_horario(elegibles, modelo, ahora, reglas):
    horarios = policy.horarios_validos(ahora, reglas)
    marco = features.marco_horarios(elegibles, horarios)
    minimo = elegibles["ultimo_contacto"].map(lambda u: policy.primer_horario_permitido(u, ahora, reglas))
    marco["minimo"] = marco["indice_lead"].map(minimo)
    marco = marco[marco["horario"] >= marco["minimo"]].reset_index(drop=True)
    if marco.empty:
        return marco
    marco["prob"] = modelo.probabilidad(marco)
    return marco


def _asignar_horarios(marco, orden, nunca_contactado, capacidad_hora):
    restante = {}
    por_lead = {i: g.sort_values("horario") for i, g in marco.groupby("indice_lead")}
    asignados = []
    for indice in orden:
        candidatos = por_lead.get(indice)
        if candidatos is None:
            continue
        libres = candidatos[
            candidatos["horario"].map(lambda h: restante.get(h, capacidad_hora) > 0)
        ]
        if libres.empty:
            continue
        if nunca_contactado[indice]:
            fila = libres.iloc[0]
        else:
            fila = libres.loc[libres["prob"].idxmax()]
        restante[fila["horario"]] = restante.get(fila["horario"], capacidad_hora) - 1
        asignados.append(fila.to_dict())
    if not asignados:
        return pd.DataFrame()
    return pd.DataFrame(asignados).set_index("indice_lead")


def calcular_asignacion(df, modelo, ahora, reglas=REGLAS):
    """Evalua elegibilidad, calcula la probabilidad por horario y asigna un horario a cada lead.

    Devuelve (elegibles, marco, asignados, excluidos). `marco` tiene una fila por lead y horario
    posible con su probabilidad; `asignados` una fila por lead con el horario elegido.
    """
    ahora = pd.Timestamp(ahora)
    evaluado = policy.evaluar_elegibilidad(df, ahora, reglas)
    excluidos = evaluado[evaluado["motivo_exclusion"].notna()].copy()
    excluidos["motivo"] = excluidos["motivo_exclusion"].map(policy.MOTIVOS)
    excluidos = excluidos[["lead_id", "canal", "resultado", "motivo_exclusion", "motivo"]]

    elegibles = evaluado[evaluado["motivo_exclusion"].isna()].copy()
    elegibles["intento"] = elegibles["intentos_previos"] + 1
    elegibles["nunca_contactado"] = elegibles["intentos_previos"].eq(0)
    marco = _probabilidades_por_horario(elegibles, modelo, ahora, reglas)
    if marco.empty:
        return elegibles, marco, pd.DataFrame(), excluidos

    por_lead = marco.groupby("indice_lead")["prob"]
    elegibles["prob_max"] = por_lead.max()
    elegibles["prob_promedio"] = por_lead.mean()
    elegibles = elegibles.sort_values(
        ["nunca_contactado", "dias_desde_registro", "prob_max"], ascending=[False, False, False]
    )
    asignados = _asignar_horarios(
        marco, list(elegibles.index), elegibles["nunca_contactado"].to_dict(), reglas.capacidad_por_hora
    )
    return elegibles, marco, asignados, excluidos


def generar_lista(df, modelo, ahora, reglas=REGLAS, cliente_llm=None, comparar_variantes=True):
    ahora = pd.Timestamp(ahora)
    elegibles, marco, asignados, excluidos = calcular_asignacion(df, modelo, ahora, reglas)
    if marco.empty:
        return pd.DataFrame(columns=COLUMNAS_LISTA), excluidos

    lista = elegibles.copy()
    lista["prioridad"] = range(1, len(lista) + 1)
    lista["horario_asignado"] = asignados["horario"].reindex(lista.index) if len(asignados) else pd.NaT
    lista["prob_asignada"] = asignados["prob"].reindex(lista.index) if len(asignados) else float("nan")
    lista["accion"] = lista["horario_asignado"].notna().map({True: "contactar", False: "en_cola"})

    aportes = modelo.contribuciones(asignados) if len(asignados) else None
    motivos, textos, origenes, etapas, variantes = [], [], [], [], []
    for indice, fila in lista.iterrows():
        if fila["accion"] == "en_cola":
            motivos.append("Sin horario libre en los próximos días: se reprograma sin descartarlo.")
            textos.append("")
            origenes.append("")
            etapas.append("")
            variantes.append("")
            continue
        asignado = asignados.loc[indice].to_dict()
        asignado["prob_promedio"] = fila["prob_promedio"]
        motivos.append(_explicar(asignado, aportes.loc[indice], fila["nunca_contactado"]))
        contexto = {
            "intento": int(fila["intento"]),
            "nunca_contactado": bool(fila["nunca_contactado"]),
            "ultimo_intento": int(fila["intento"]) >= reglas.max_intentos,
            "franja_dia": _franja_texto(fila["horario_asignado"], ahora),
        }
        if not pd.isna(fila["asesor"]):
            contexto["asesor"] = fila["asesor"]
        etapa = mensajes.etapa_de(contexto)
        variante = mensajes.elegir_variante(fila["lead_id"], etapa) if comparar_variantes else "A"
        contexto["variante"] = variante
        contexto["origen_ia"] = "agente" in str(fila["canal"]).lower()
        contexto["dias"] = int(fila["dias_desde_registro"])
        texto, origen = mensajes.generar_mensaje(contexto, cliente_llm)
        textos.append(texto)
        origenes.append(origen)
        etapas.append(etapa)
        variantes.append("LLM" if origen == "llm" else variante)
    lista["motivo"] = motivos
    lista["mensaje"] = textos
    lista["origen_mensaje"] = origenes
    lista["etapa"] = etapas
    lista["variante"] = variantes
    lista["dias_desde_registro"] = lista["dias_desde_registro"].round(1)
    return lista[COLUMNAS_LISTA].reset_index(drop=True), excluidos
