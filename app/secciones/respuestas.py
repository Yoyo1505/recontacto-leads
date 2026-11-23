"""Seccion RESPUESTAS: que entiende la herramienta de lo que contesta una persona y que haria.

Que muestra
    Una caja para escribir una respuesta (o elegir un ejemplo) y, debajo, la intencion detectada, el motivo,
    la accion, lo que propone la persona (dia u hora) y si lo debe atender un asesor.

Como leerla
    Es un clasificador por reglas, sin modelo: cada decision se puede leer. Ante la duda pasa la
    conversacion a un asesor. Seguridad (malestar o emergencia) va antes que baja, y baja antes que todo.
    No envia mensajes ni se conecta a ningun canal; para aplicar una baja o un cambio de estado usa
    `python -m recontacto.respuestas --texto "..." --lead L00001 --aplicar`.

Donde cambiar cosas
    - Reglas de lectura y respuestas sugeridas: `recontacto/respuestas.py`.
    - Ejemplos del menu: `recontacto/respuestas.py` (`EJEMPLOS`).
"""

from componentes import encabezado, nota, tarjeta
from dash import Input, Output, dcc, html

from recontacto import respuestas

ID = "respuestas"
TITULO = "Respuestas"
RUTA = "/respuestas"

NOMBRES_INTENCION = {
    "baja": "Pide no recibir más mensajes",
    "no_interesado": "No le interesa",
    "interes": "Quiere seguir",
    "agenda": "Propone un día u hora",
    "posponer": "Pide otro momento",
    "pregunta": "Hace una pregunta",
    "seguridad": "Menciona un malestar o emergencia",
    "ambigua": "No se entiende",
}


def resultado(texto):
    if not texto or not texto.strip():
        return html.P("Escribe una respuesta o elige un ejemplo.", className="ayuda")
    c = respuestas.clasificar(texto)
    propuesta = " ".join(p for p in (c.dia, f"a las {c.hora}:00" if c.hora >= 0 else "", c.franja) if p)
    filas = [
        html.P([html.B(NOMBRES_INTENCION.get(c.intencion, c.intencion)), f" · confianza {c.confianza}"]),
        html.P([html.B("Por qué: "), c.motivo]),
        html.P([html.B("Qué hace la herramienta: "), c.accion]),
    ]
    if propuesta:
        filas.append(html.P([html.B("Lo que propone la persona: "), propuesta]))
    filas.append(html.P([html.B("¿Lo atiende un asesor? "), "Sí" if c.requiere_humano else "No"]))
    if c.respuesta_sugerida:
        filas.append(html.P([html.B("Respuesta sugerida (la envía el asesor): "), c.respuesta_sugerida], className="nota"))
    return html.Div(filas, id="resp-detalle")


def layout(ctx):
    return [
        encabezado("Respuestas", "Qué entiende la herramienta de lo que contesta una persona."),
        tarjeta(
            dcc.Dropdown(id="resp-ejemplo", options=[{"label": e, "value": e} for e in respuestas.EJEMPLOS], placeholder="Elige un ejemplo"),
            dcc.Input(id="resp-texto", type="text", placeholder="O escribe lo que contesta la persona", debounce=True, className="entrada", style={"width": "100%", "marginTop": "10px"}),
            html.Button("Interpretar", id="resp-boton", n_clicks=0, className="boton"),
            titulo="Probar una respuesta",
            ayuda="Clasificador por reglas, sin modelo. Ante la duda, pasa la conversación a un asesor.",
        ),
        tarjeta(html.Div(id="resp-resultado", children=resultado("")), titulo="Qué entendió y qué hace"),
        nota("No envía mensajes ni se conecta a WhatsApp. Para aplicar una baja usa la línea de comandos o la sección Datos."),
    ]


def registrar(app, ctx):
    @app.callback(Output("resp-texto", "value"), Input("resp-ejemplo", "value"), prevent_initial_call=True)
    def elegir_ejemplo(ejemplo):
        return ejemplo or ""

    @app.callback(
        Output("resp-resultado", "children"),
        Input("resp-boton", "n_clicks"),
        Input("resp-texto", "value"),
    )
    def interpretar(clics, texto):
        return resultado(texto)
