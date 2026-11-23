"""Lectura de las respuestas de las personas: que quisieron decir y que debe pasar.

Para que sirve
    Cuando alguien contesta un mensaje ("NO", "sí, llámame a las 4", "¿cuánto cuesta?"), la
    herramienta lo interpreta y propone la accion: registrar una baja, pasar a la persona a
    seguimiento, agendar una hora o pasar la conversacion a un asesor.

Principios (el trato primero)
    - "NO" es una baja: la persona respondio a la linea que le ofrecimos para dejar de recibir mensajes.
    - Ante la duda, se pasa a un asesor. Nada ambiguo se responde solo.
    - Las preguntas (precio, tratamiento, medicamentos) y todo lo que suene a malestar o emergencia
      las atiende una persona; la herramienta nunca da informacion medica ni de precios.
    - Solo se contesta automaticamente con textos fijos y neutros (confirmar una baja, agradecer).

Es un clasificador por reglas, sin modelo: cada decision se puede leer y probar.

Donde cambiar cosas
    - Frases que activan cada intencion: constantes PATRON_*.
    - Que hace cada intencion: ACCIONES.
    - Orden de prioridad: funcion `clasificar`.
Uso desde la linea de comandos
    python -m recontacto.respuestas --texto "sí, llámame mañana a las 4"
    python -m recontacto.respuestas --lead L00123 --texto "NO" --aplicar
"""

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass

DIAS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}


def _limpio(texto):
    normal = unicodedata.normalize("NFD", str(texto))
    sin = "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()
    sin = re.sub(r"\b([ap])\.\s?m\.?", r"\1m", sin)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_:?¿!¡ ]", " ", sin)).strip()


PATRON_SEGURIDAD = re.compile(r"\b(emergencia|urgencia medica|me siento mal|dolor fuerte|ayuda urgente|no me siento bien|suicid\w*|mareo\w*|desmay\w*)\b")
PATRON_BAJA = re.compile(
    r"^(no|n o|stop|baja|cancelar|cancela)$|\b(no (me )?(escriban|escribas|escriba|contacten|contactes|manden|molesten)|dejen de|deja de|no quiero (mas )?(mensajes|que me escriban|que me contacten)|ya no (me )?(escriban|escribas|contacten)|quiten mi numero|borren mi numero|no mas mensajes)\b"
)
PATRON_NO_INTERESADO = re.compile(r"\b(no me interesa|ya no me interesa|no estoy interesad\w*|no gracias|ya no necesito|no lo necesito|no por ahora gracias)\b")
PATRON_POSPONER = re.compile(r"\b(ahorita no|ahora no|mas tarde|otro dia|despues|luego|en otro momento|ahora no puedo|no puedo ahora|estoy ocupad\w*)\b")
PATRON_NEGACION_TIEMPO = re.compile(r"\b(no puedo|no podre|no voy a poder|no puedes|ahorita no|ahora no)\b")
PATRON_INTERES = re.compile(r"^(si|sii+|claro|ok|okay|dale|adelante|por favor|va|sale|perfecto|de acuerdo)\b|\b(me interesa|quiero (mas )?informacion|llamame|llamenme|marcame|marquenme|escribeme|mandame (la )?informacion|si quiero|me gustaria)\b")
PATRON_PREGUNTA = re.compile(r"\?|\b(cuanto|cuanta|cuales|cual|que incluye|precio|costo|cuesta|como funciona|tienen|incluye|medicamento|tratamiento|receta|puedo|donde)\b")
PATRON_PREGUNTA_FUERTE = re.compile(r"\?|\b(cuanto|cuanta|precio|costo|cuesta|incluye|medicamento|tratamiento|receta)\b")
PATRON_HORA_EXPLICITA = re.compile(r"\b(?:a las|a la|como a las|tipo|a eso de las|despues de las)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|h|hrs|horas)?\b")
PATRON_HORA_SUFIJO = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|h|hrs|horas)\b")
PATRON_HORA_DOSPUNTOS = re.compile(r"\b(\d{1,2}):(\d{2})\b")
PATRON_FRANJA = re.compile(r"\b(en la manana|por la manana|de manana|en la tarde|por la tarde|en la noche|por la noche)\b")


@dataclass
class Clasificacion:
    intencion: str
    accion: str
    estado_nuevo: str
    baja: bool
    requiere_humano: bool
    respuesta_sugerida: str
    confianza: str
    dia: str = ""
    hora: int = -1
    franja: str = ""
    motivo: str = ""


ACCIONES = {
    "seguridad": ("Pasar de inmediato a un asesor", "", False, True, "Gracias por escribir. Si es una emergencia médica, llama al 911. Un asesor te contactará en cuanto pueda."),
    "baja": ("Registrar la baja y confirmar", "", True, False, "Entendido, no te volveremos a escribir. Gracias por tu tiempo."),
    "no_interesado": ("Marcar como no interesado y agradecer", "no_interesado", False, False, "Gracias por avisarnos. Si más adelante cambias de opinión, aquí estaremos."),
    "agenda": ("Pasar a seguimiento y agendar la hora", "en_seguimiento", False, False, ""),
    "interes": ("Pasar a seguimiento: la conversación sigue con el asesor", "en_seguimiento", False, False, ""),
    "posponer": ("Reprogramar el siguiente intento", "", False, False, ""),
    "pregunta": ("Pasar a un asesor: la herramienta no responde preguntas", "", False, True, ""),
    "ambigua": ("Pasar a un asesor para revisar", "", False, True, ""),
}
NOMBRES_FRANJA = {"manana": "mañana", "tarde": "tarde", "noche": "noche"}
EJEMPLOS = [
    "NO",
    "Sí, llámame mañana a las 4",
    "¿Cuánto cuesta?",
    "Ahorita no puedo",
    "Me siento mal desde ayer",
    "No gracias, ya no me interesa",
    "Mejor el lunes por la mañana",
    "Hola",
]


def _hora(limpio):
    franja = PATRON_FRANJA.search(limpio)
    hora, sufijo = -1, None
    for patron in (PATRON_HORA_EXPLICITA, PATRON_HORA_SUFIJO, PATRON_HORA_DOSPUNTOS):
        m = patron.search(limpio)
        if m:
            hora = int(m.group(1))
            sufijo = m.group(3) if patron is not PATRON_HORA_DOSPUNTOS else None
            break
    if not 0 <= hora <= 23:
        hora = -1
    if hora >= 0:
        if sufijo == "pm" and hora < 12:
            hora += 12
        elif sufijo is None and franja and franja.group(1).endswith(("tarde", "noche")) and hora < 12:
            hora += 12
        elif sufijo is None and not franja and 1 <= hora <= 7:
            hora += 12
    nombre = NOMBRES_FRANJA[franja.group(1).split()[-1]] if franja else ""
    return hora, nombre


def _dia(limpio):
    if re.search(r"\bpasado manana\b", limpio):
        return "pasado mañana"
    if re.search(r"\bmanana\b", limpio) and not re.search(r"(en la|por la|de) manana", limpio):
        return "mañana"
    if re.search(r"\bhoy\b", limpio):
        return "hoy"
    for nombre in DIAS:
        if re.search(rf"\b{nombre}\b", limpio):
            return {"miercoles": "miércoles", "sabado": "sábado"}.get(nombre, nombre)
    return ""


def clasificar(texto):
    limpio = _limpio(texto)
    if not limpio:
        return _armar("ambigua", "baja", "Respuesta vacía")
    if PATRON_SEGURIDAD.search(limpio):
        return _armar("seguridad", "alta", "Menciona malestar o una emergencia")
    if PATRON_BAJA.search(limpio):
        return _armar("baja", "alta", "Pide no recibir más mensajes")
    if PATRON_NO_INTERESADO.search(limpio):
        return _armar("no_interesado", "alta", "Dice que no le interesa")
    hora, franja = _hora(limpio)
    dia = _dia(limpio)
    pregunta = bool(PATRON_PREGUNTA.search(limpio))
    if PATRON_NEGACION_TIEMPO.search(limpio) and hora < 0:
        return _armar("posponer", "media", "Dice que no puede en este momento", dia, hora, franja)
    if hora >= 0 or dia or franja:
        extra = bool(PATRON_PREGUNTA_FUERTE.search(limpio))
        motivo = "Propone un día u hora" + (" y además hace una pregunta" if extra else "")
        return _armar("agenda", "alta" if (hora >= 0 or dia) else "media", motivo, dia, hora, franja, humano_extra=extra)
    if PATRON_POSPONER.search(limpio):
        return _armar("posponer", "media", "Pide hablar en otro momento")
    if PATRON_INTERES.search(limpio):
        return _armar("interes", "alta", "Responde que sí o pide información", humano_extra=pregunta)
    if pregunta:
        return _armar("pregunta", "media", "Hace una pregunta")
    return _armar("ambigua", "baja", "No se entiende con claridad")


def _armar(intencion, confianza, motivo, dia="", hora=-1, franja="", humano_extra=False):
    accion, estado, baja, humano, respuesta = ACCIONES[intencion]
    humano = humano or humano_extra
    if intencion == "agenda":
        cuando = " ".join(p for p in (dia, f"a las {hora}:00" if hora >= 0 else "", f"por la {franja}" if franja and hora < 0 else "") if p)
        respuesta = "" if humano else (f"Perfecto, quedamos {cuando}. Gracias por contestar." if cuando else "Perfecto, gracias por contestar.")
    return Clasificacion(intencion, accion, estado, baja, humano, respuesta, confianza, dia, hora, franja, motivo)


def aplicar(clasificacion, lead_id, telefono, ruta_datos=None):
    """Aplica la decision a los datos: baja o cambio de estado. Devuelve un texto con lo que se hizo."""
    import pandas as pd

    from . import config, ingesta

    hecho = []
    if clasificacion.baja:
        nueva = ingesta.agregar_baja(telefono)
        hecho.append("baja registrada" if nueva else "el teléfono ya estaba en la lista de bajas")
    if clasificacion.estado_nuevo:
        actual = ingesta.leer_canonico(ruta_datos or config.ruta_datos_activa())
        fila = actual[actual["lead_id"] == lead_id]
        if fila.empty:
            raise ingesta.ErrorIngesta(f"No existe el lead {lead_id}")
        cambio = fila.iloc[0].to_dict()
        cambio["resultado"] = clasificacion.estado_nuevo
        cambio = {("estado" if k == "entidad" else k): v for k, v in cambio.items()}
        informe = ingesta.procesar(pd.DataFrame([cambio]), "respuesta", base=actual)
        ingesta.aplicar(informe)
        hecho.append(f"estado cambiado a {clasificacion.estado_nuevo}")
    return "; ".join(hecho) or "sin cambios en los datos"


def main(argumentos=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Interpreta la respuesta de una persona")
    parser.add_argument("--texto", required=True)
    parser.add_argument("--lead")
    parser.add_argument("--telefono")
    parser.add_argument("--aplicar", action="store_true", help="aplica la decision a los datos (necesita --lead)")
    args = parser.parse_args(argumentos)
    c = clasificar(args.texto)
    print(f"Intención: {c.intencion} (confianza {c.confianza}): {c.motivo}")
    print(f"Acción: {c.accion}")
    if c.dia or c.hora >= 0 or c.franja:
        propuesta = " ".join(p for p in (c.dia, f"a las {c.hora}:00" if c.hora >= 0 else "", c.franja) if p)
        print(f"Propuesta de la persona: {propuesta}")
    print(f"Requiere asesor: {'sí' if c.requiere_humano else 'no'}")
    if c.respuesta_sugerida:
        print(f"Respuesta sugerida: {c.respuesta_sugerida}")
    if args.aplicar:
        if not args.lead:
            print("Para aplicar indica --lead.")
            return 2
        from . import config
        from .data import cargar_leads

        base = cargar_leads(config.ruta_datos_activa())
        fila = base[base["lead_id"] == args.lead]
        telefono = args.telefono or (fila.iloc[0]["telefono"] if len(fila) else "")
        print("Aplicado:", aplicar(c, args.lead, telefono))
    return 0


if __name__ == "__main__":
    sys.exit(main())
