"""Seccion MENSAJES: que mensaje recibe cada persona segun su situacion.

Que muestra
    - La biblioteca completa: tres pasos (primer contacto, retomar, cierre) con variantes A, B y C, la
      estrategia de cada una y un ejemplo del texto.
    - Si cada texto cumple las reglas de seguridad (sin salud, sin promesas, con baja y con marca).
    - Cuantas personas necesita comparar la prueba de variantes.

Como leerla
    A cada persona le toca siempre la misma variante (se asigna por su lead_id). Que una variante recupere
    mas conversaciones que otra es una hipotesis: hoy los datos no registran que mensaje se envio.

Donde cambiar cosas
    - Textos y estrategias: `recontacto/mensajes.py` (`BIBLIOTECA` y `ESTRATEGIAS`).
    - Reglas de validacion: `recontacto/mensajes.py` (`validar_mensaje`, `validar_fidelidad`).
    - Efectos para el tamano de muestra: constante `EFECTOS_VARIANTES`.
"""

from componentes import encabezado, nota, tarjeta
from dash import html

from recontacto import mensajes
from recontacto import simulacion as sim

ID = "mensajes"
TITULO = "Mensajes"
RUTA = "/mensajes"

EFECTOS_VARIANTES = (0.05, 0.08)
NOMBRES_ETAPA = {"primer_contacto": "Primer contacto", "retoma": "Retomar", "cierre": "Cierre"}
A_QUIEN = {
    "primer_contacto": "A quien nunca recibió un contacto",
    "retoma": "A quien no contestó el primer intento",
    "cierre": "Al último intento permitido",
}
REGLAS = [
    "No menciona la condición de salud, no promete resultados, no mete urgencia ni enlaces.",
    "Menciona la marca y trae la forma de pedir que no se le escriba más.",
    "Hasta 480 caracteres, en tono de tú, y siempre habla de la solicitud de información.",
    "Cambia si la solicitud llegó por un asistente de IA y si pasaron varios días desde la solicitud.",
    "El tercer mensaje avisa que no se insistirá más.",
]


def filas_biblioteca():
    return mensajes.biblioteca_validada()


def tabla_biblioteca(filas):
    encabezados = html.Tr([html.Th(t) for t in ("Situación", "Variante", "Mensaje de ejemplo", "Reglas")])
    cuerpo = []
    for f in filas:
        cuerpo.append(
            html.Tr(
                [
                    html.Td([NOMBRES_ETAPA[f["etapa"]], html.Div(A_QUIEN[f["etapa"]], className="ayuda")]),
                    html.Td([html.B(f["variante"]), html.Div(f["estrategia"], className="ayuda")]),
                    html.Td(f["texto"]),
                    html.Td("Válido" if f["valido"] else "Revisar", className="insignia ok" if f["valido"] else "insignia mal"),
                ]
            )
        )
    return html.Table([html.Thead(encabezados), html.Tbody(cuerpo)], className="tabla")


def layout(ctx):
    filas = filas_biblioteca()
    p0 = ctx.tasa_contesta
    muestras = [f"{round(sim.tamano_muestra(p0, d)):,} personas por variante para detectar {d * 100:.0f} puntos" for d in EFECTOS_VARIANTES]
    return [
        encabezado("Mensajes", "Qué mensaje recibe cada persona según su situación."),
        tarjeta(
            tabla_biblioteca(filas),
            titulo="Biblioteca por situación",
            ayuda="Cada paso tiene varias redacciones con una estrategia distinta. A cada persona le toca siempre la misma, para poder comparar.",
        ),
        tarjeta(html.Ul([html.Li(r) for r in REGLAS]), titulo="Reglas que todo mensaje cumple"),
        tarjeta(
            html.Ul([html.Li(m) for m in muestras]),
            titulo="Cómo se sabrá cuál variante recupera más",
            ayuda="Se guarda la variante enviada (columna variante) y se compara contra la A con una prueba de dos proporciones.",
        ),
        nota("Hoy no hay datos de cuál variante funciona mejor: es una hipótesis por probar, no un resultado."),
    ]


def registrar(app, ctx):
    return None
