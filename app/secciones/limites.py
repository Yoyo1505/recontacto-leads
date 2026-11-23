"""Seccion LIMITES: lo que los datos no permiten afirmar y los supuestos.

Que muestra
    Tres listas en texto: lo que no se puede afirmar, los supuestos que no son datos y los datos
    que harian falta. Es contenido editable, sin calculos.

Donde cambiar cosas
    - Edita las listas `NO_AFIRMAR`, `SUPUESTOS` y `DATOS_FALTANTES`.
"""

from componentes import encabezado, nota, tarjeta
from dash import html

ID = "limites"
TITULO = "Límites"
RUTA = "/limites"

NO_AFIRMAR = [
    "Que un mensaje convenza más que otro: hay un solo intento de contacto por lead y no se registró el mensaje usado.",
    "Que el horario, por sí mismo, haga contestar más: en los datos, la hora del contacto y la rapidez del contacto van juntas.",
    "Que un asesor sea mejor o peor: las diferencias entre asesores caben dentro del azar (ver gráfico de embudo).",
    "Que la ventaja del modelo sea detectable en un solo día: la simulación muestra un intervalo que incluye el cero.",
]
SUPUESTOS = [
    "Ventana de recuperación de 21 días, máximo de 3 intentos, 24 h entre intentos y 15 contactos por hora.",
    "Horario de 9:00 a 20:00 de lunes a sábado.",
    "La parte causal de la ventaja del horario (alpha) se explora de 0 a 1; no se conoce.",
    "La conversión a venta de quien contesta es la histórica por canal, suavizada hacia el promedio global.",
]
DATOS_FALTANTES = [
    "Segundos intentos y su resultado.",
    "Texto del mensaje enviado y hora de apertura.",
    "Motivo cuando alguien dice que no le interesa.",
    "Origen del lead cuando llega por un agente de inteligencia artificial.",
]


def lista(titulo, elementos):
    return tarjeta(html.Ul([html.Li(e) for e in elementos]), titulo=titulo)


def layout(ctx):
    return [
        encabezado("Límites", "Qué se puede afirmar con estos datos y qué no."),
        lista("Lo que no se puede afirmar", NO_AFIRMAR),
        lista("Supuestos que no son datos", SUPUESTOS),
        lista("Datos que harían falta", DATOS_FALTANTES),
        nota("Las reglas de trato y las decisiones técnicas están documentadas en docs/README.md y docs/bitacora.md."),
    ]


def registrar(app, ctx):
    return None
