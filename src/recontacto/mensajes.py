"""Biblioteca de mensajes por situacion, con variantes comparables, y su validador.

Situaciones (etapas)
    primer_contacto   a quien nunca recibio un contacto
    retoma            a quien no contesto el primer intento
    cierre            al ultimo intento permitido

Variantes
    Cada situacion tiene varias redacciones con una estrategia distinta (A, B, C). Se asigna una por
    persona de forma estable (mismo lead, misma variante) para poder comparar despues cuanto
    recupera cada una. `variante` se guarda en los datos (columna opcional) junto con el resultado.

Reglas que todo mensaje cumple (las revisa `validar_mensaje`)
    - No menciona la condicion de salud, no promete resultados, no mete urgencia ni enlaces.
    - Menciona la marca y trae la forma de pedir que no se le escriba mas.
    - Maximo 480 caracteres.

Contexto que puede llegar a un modelo de lenguaje: solo los campos de CAMPOS_PERMITIDOS, nunca
telefono, edad, diagnostico ni nombre de la persona.

Donde cambiar cosas
    - Textos y variantes: BIBLIOTECA y ESTRATEGIAS.
    - Palabras prohibidas: PATRONES_PROHIBIDOS.
    - Como se reparten las variantes: elegir_variante.
"""

import json
import re
import unicodedata
import zlib
from dataclasses import dataclass, field

from . import config

CAMPOS_PERMITIDOS = frozenset(
    {"intento", "nunca_contactado", "ultimo_intento", "franja_dia", "asesor", "variante", "origen_ia", "dias"}
)
LONGITUD_MAXIMA = 480
BAJA = "Si prefieres que no te escribamos, responde NO."

BIBLIOTECA = {
    "primer_contacto": {
        "A": "{recibimos} y con gusto te la compartimos. ¿Te parece bien si te llamamos {franja}?",
        "B": "{recibimos}. ¿Prefieres que te llamemos o que te escribamos por aquí? Dime qué te acomoda mejor.",
        "C": "{recibimos}. En una llamada corta te explico cómo funciona y resuelvo tus dudas. ¿Cuándo te viene bien?",
    },
    "retoma": {
        "A": "Intenté comunicarme contigo por tu solicitud de información y no logramos hablar. Cuando tengas un momento, dime si prefieres que te llame o seguir por mensaje.",
        "B": "Te busqué por tu solicitud de información y no pudimos hablar. ¿Te escribo con la información por aquí, o prefieres que te llame {franja}?",
        "C": "Sigo con tu solicitud de información a la mano. ¿Quieres que la retomemos? Con un «sí» te busco en el horario que prefieras.",
    },
    "cierre": {
        "A": "Este es mi último mensaje sobre tu solicitud de información, para no insistirte. Si más adelante quieres retomarla, aquí estaremos.",
        "B": "No quiero molestarte, así que este es mi último mensaje. Tu solicitud queda guardada: cuando quieras retomarla, solo respóndeme aquí.",
    },
}
ESTRATEGIAS = {
    "primer_contacto": {"A": "propone un horario concreto", "B": "deja elegir el canal", "C": "explica el siguiente paso y pregunta cuándo"},
    "retoma": {"A": "da el control sobre cómo seguir", "B": "ofrece las dos opciones con horario", "C": "pide un sí sencillo"},
    "cierre": {"A": "libera la presión", "B": "deja la solicitud guardada"},
}

PATRONES_PROHIBIDOS = {
    "menciona la condicion de salud": r"\b(diabet\w*|obesidad|sobrepeso|peso|kilos?|kg|glucosa|enfermedad\w*)\b",
    "promete resultados": r"\b(cura\w*|curar\w*|garantiz\w*|milagro\w*|sin esfuerzo|100%)\b",
    "presiona con urgencia": r"\b(ultima oportunidad|solo hoy|urgente|oferta|descuento|promocion)\b",
    "incluye enlaces": r"(https?://|www\.)",
}

SISTEMA = (
    "Eres un asistente que redacta mensajes breves de WhatsApp en español de México para el equipo de "
    f"asesores de {config.MARCA}, una empresa de salud digital. La persona pidió información y no pudimos hablar con ella. "
    "Reglas obligatorias: tono cordial y respetuoso; máximo tres frases más la línea de baja; no menciones "
    "enfermedades, diagnósticos, peso ni resultados; no prometas nada; no presiones ni uses urgencia; no inventes "
    "datos; no incluyas enlaces; menciona a la marca por su nombre; termina siempre con la frase exacta "
    "'Si prefieres que no te escribamos, responde NO.'. "
    "Si es el último intento, aclara que no insistirás más. Devuelve solo el texto del mensaje."
)


@dataclass
class ResultadoValidacion:
    valido: bool
    problemas: list = field(default_factory=list)


def _sin_acentos(texto):
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()


ESTRATEGIA_REQUERIDA = {
    ("primer_contacto", "A"): [r"llam"],
    ("primer_contacto", "B"): [r"llam", r"escrib"],
    ("primer_contacto", "C"): [r"llamada", r"cuando"],
    ("retoma", "A"): [r"llam", r"mensaje"],
    ("retoma", "B"): [r"llam", r"escrib"],
    ("retoma", "C"): [r"retom"],
    ("cierre", "A"): [r"ultimo"],
    ("cierre", "B"): [r"ultimo"],
}
TRATO_DE_USTED = r"\b(usted|ustedes|ayudarlo|ayudarla|apoyarlo|apoyarla|le escribimos|le podemos|le invito|necesita|desea|su solicitud)\b"


def validar_fidelidad(texto, contexto):
    """Comprueba que el texto siga la situacion y la estrategia de la variante, no solo las reglas de seguridad."""
    limpio = _sin_acentos(texto)
    problemas = []
    if "solicitud" not in limpio:
        problemas.append("no menciona la solicitud de informacion")
    etapa = etapa_de(contexto)
    letra = contexto.get("variante") or "A"
    for patron in ESTRATEGIA_REQUERIDA.get((etapa, letra), []):
        if not re.search(patron, limpio):
            problemas.append(f"no sigue la estrategia de la variante {letra} ({etapa})")
            break
    if re.search(TRATO_DE_USTED, limpio):
        problemas.append("mezcla el trato de usted con el de tu")
    return problemas


def validar_mensaje(texto, contexto=None):
    problemas = []
    limpio = _sin_acentos(texto)
    if not texto.strip():
        problemas.append("esta vacio")
    if len(texto) > LONGITUD_MAXIMA:
        problemas.append("es demasiado largo")
    if "responde no" not in limpio:
        problemas.append("no incluye la opcion de baja")
    if _sin_acentos(config.MARCA) not in limpio:
        problemas.append("no menciona la marca")
    for nombre, patron in PATRONES_PROHIBIDOS.items():
        if re.search(patron, limpio):
            problemas.append(nombre)
    if contexto is not None:
        problemas.extend(validar_fidelidad(texto, contexto))
    return ResultadoValidacion(valido=not problemas, problemas=problemas)


def _verificar_contexto(contexto):
    sobrantes = set(contexto) - CAMPOS_PERMITIDOS
    if sobrantes:
        raise ValueError(f"Campos no permitidos en el contexto del mensaje: {sorted(sobrantes)}")


def etapa_de(contexto):
    if contexto.get("nunca_contactado"):
        return "primer_contacto"
    if contexto.get("ultimo_intento"):
        return "cierre"
    return "retoma"


def elegir_variante(lead_id, etapa):
    """Variante estable por persona y etapa: el mismo lead recibe siempre la misma."""
    letras = sorted(BIBLIOTECA[etapa])
    return letras[zlib.crc32(f"{lead_id}:{etapa}".encode("utf-8")) % len(letras)]


def _saludo_asesor(contexto):
    asesor = contexto.get("asesor")
    if asesor:
        return f"Hola, te escribe {asesor} de {config.MARCA}."
    return f"Hola, te escribimos de {config.MARCA}."


def plantilla(contexto):
    _verificar_contexto(contexto)
    etapa = etapa_de(contexto)
    letra = contexto.get("variante") or "A"
    if letra not in BIBLIOTECA[etapa]:
        letra = "A"
    if contexto.get("origen_ia"):
        recibimos = "Recibimos la solicitud de información que enviaste a través de un asistente de inteligencia artificial"
    else:
        recibimos = "Recibimos tu solicitud de información"
    cuerpo = BIBLIOTECA[etapa][letra].format(recibimos=recibimos, franja=contexto.get("franja_dia", "hoy"))
    if etapa != "cierre" and (contexto.get("dias") or 0) >= 3:
        cuerpo = "Sé que pasaron unos días desde tu solicitud. " + cuerpo
    return f"{_saludo_asesor(contexto)} {cuerpo} {BAJA}"


def construir_prompt(contexto):
    """Pide al modelo que reescriba la plantilla con sus palabras, sin cambiar la estrategia."""
    _verificar_contexto(contexto)
    etapa = etapa_de(contexto)
    letra = contexto.get("variante") or "A"
    if letra not in BIBLIOTECA[etapa]:
        letra = "A"
    base = plantilla({**contexto, "variante": letra})
    return (
        "Datos del mensaje a redactar (JSON): " + json.dumps(contexto, ensure_ascii=False) + "\n"
        f"Situación: {etapa}. Estrategia: {ESTRATEGIAS[etapa][letra]}.\n"
        "Reescribe este texto con tus palabras: tutea a la persona, menciona su solicitud de información, "
        "conserva la estrategia y termina con la línea de baja exacta.\n"
        "Texto base:\n" + base
    )


def generar_mensaje(contexto, cliente=None):
    _verificar_contexto(contexto)
    if cliente is not None:
        texto = cliente.generar(SISTEMA, construir_prompt(contexto))
        if texto:
            texto = texto.strip().strip('"').strip()
            if validar_mensaje(texto, contexto).valido:
                return texto, "llm"
    return plantilla(contexto), "plantilla"


def biblioteca_validada():
    """Todas las plantillas con una situacion de ejemplo, para comprobar que cumplen las reglas."""
    filas = []
    for etapa, variantes in BIBLIOTECA.items():
        for letra in sorted(variantes):
            contexto = {"nunca_contactado": etapa == "primer_contacto", "ultimo_intento": etapa == "cierre", "variante": letra, "franja_dia": "hoy por la tarde", "asesor": "Asesor B"}
            texto = plantilla(contexto)
            filas.append({"etapa": etapa, "variante": letra, "estrategia": ESTRATEGIAS[etapa][letra], "texto": texto, "valido": validar_mensaje(texto).valido})
    return filas
