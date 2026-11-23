"""Punto de entrada de la aplicacion Dash.

Ejecutar
    python app/dash_app.py            abre http://127.0.0.1:8050
    python app/dash_app.py --puerto 8060

Estructura
    contexto.py        datos, modelo y calculos en cache (compartidos)
    tema.py            colores y estilo de las graficas
    componentes.py     piezas reutilizables (tarjeta, KPI, grafica)
    secciones/         una pagina por archivo; ver secciones/__init__.py
    assets/            estilo.css y logo (Dash los sirve solo)

Este archivo solo ensambla: encabezado, barra lateral con las reglas de trato, enrutamiento por
direccion y el estado compartido (fecha y reglas) que leen todas las secciones.

Donde cambiar cosas
    - Controles de la barra lateral: funcion `panel_reglas` y callback `reunir_estado`.
    - Menu superior: se genera solo desde `secciones.SECCIONES`.
    - Titulo de la pestana del navegador: parametro `title` en `crear_app`.
"""

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "src"))
sys.path.insert(0, str(AQUI))

from contexto import Contexto, estado_inicial, reglas_a_dict  # noqa: E402
from dash import Dash, Input, Output, dcc, html, no_update  # noqa: E402
from secciones import POR_RUTA, SECCIONES  # noqa: E402

from recontacto import config  # noqa: E402
from recontacto.config import Reglas  # noqa: E402

DIAS_OPCIONES = [{"label": n[:3].capitalize(), "value": i} for i, n in enumerate(config.DIAS_SEMANA)]


def panel_reglas(ctx):
    base = config.REGLAS
    return html.Div(
        [
            html.H3("Parámetros"),
            html.Label("Fecha de la lista"),
            dcc.DatePickerSingle(id="ctl-fecha", date=ctx.fecha_inicial, display_format="DD/MM/YYYY", className="selector"),
            html.Label("Horario de contacto"),
            dcc.RangeSlider(id="ctl-horas", min=6, max=22, step=1, value=[base.hora_inicio, base.hora_fin], marks={6: "6", 14: "14", 22: "22"}, tooltip={"placement": "bottom"}),
            html.Label("Días permitidos"),
            dcc.Checklist(id="ctl-dias", options=DIAS_OPCIONES, value=list(base.dias_permitidos), inline=True, className="checks"),
            html.Label("Máximo de intentos"),
            dcc.Slider(id="ctl-intentos", min=1, max=5, step=1, value=base.max_intentos, marks={1: "1", 3: "3", 5: "5"}, tooltip={"placement": "bottom"}),
            html.Label("Horas entre intentos"),
            dcc.Slider(id="ctl-entre", min=0, max=72, step=6, value=base.horas_entre_intentos, marks={0: "0", 24: "24", 72: "72"}, tooltip={"placement": "bottom"}),
            html.Label("Ventana de recuperación (días)"),
            dcc.Slider(id="ctl-ventana", min=7, max=60, step=1, value=base.ventana_dias, marks={7: "7", 21: "21", 60: "60"}, tooltip={"placement": "bottom"}),
            html.Label("Contactos posibles por hora"),
            dcc.Slider(id="ctl-capacidad", min=1, max=40, step=1, value=base.capacidad_por_hora, marks={1: "1", 15: "15", 40: "40"}, tooltip={"placement": "bottom"}),
            html.Div(id="ctl-error", className="error"),
            html.P("Los valores son supuestos, no datos.", className="ayuda"),
        ],
        className="panel-reglas",
    )


def encabezado_app():
    return html.Header(
        [
            html.Img(src="/assets/logo-clivi.png", className="logo", alt="Clivi"),
            html.Div("Recontacto de leads", className="titulo-app"),
            html.Nav(id="menu", className="menu"),
        ],
        className="encabezado-app",
    )


def crear_app(ctx=None):
    ctx = ctx or Contexto()
    app = Dash(__name__, suppress_callback_exceptions=True, title="Recontacto de leads · Clivi")
    app.layout = html.Div(
        [
            dcc.Location(id="url"),
            dcc.Store(id="estado", data=estado_inicial(ctx)),
            encabezado_app(),
            html.Div([html.Aside(panel_reglas(ctx), className="lateral"), html.Main(id="contenido", className="contenido")], className="cuerpo"),
        ]
    )

    @app.callback(Output("contenido", "children"), Output("menu", "children"), Input("url", "pathname"))
    def mostrar(ruta):
        seccion = POR_RUTA.get(ruta or "/", SECCIONES[0])
        menu = [
            dcc.Link(s.TITULO, href=s.RUTA, className="enlace activo" if s is seccion else "enlace")
            for s in SECCIONES
        ]
        return seccion.layout(ctx), menu

    @app.callback(
        Output("estado", "data"),
        Output("ctl-error", "children"),
        Input("ctl-fecha", "date"),
        Input("ctl-horas", "value"),
        Input("ctl-dias", "value"),
        Input("ctl-intentos", "value"),
        Input("ctl-entre", "value"),
        Input("ctl-ventana", "value"),
        Input("ctl-capacidad", "value"),
    )
    def reunir_estado(fecha, horas, dias, intentos, entre, ventana, capacidad):
        try:
            reglas = Reglas(
                hora_inicio=horas[0],
                hora_fin=horas[1],
                dias_permitidos=tuple(dias or ()),
                max_intentos=intentos,
                horas_entre_intentos=entre,
                ventana_dias=ventana,
                capacidad_por_hora=capacidad,
            )
        except ValueError as error:
            return no_update, f"Reglas no válidas: {error}"
        return {"fecha": str(fecha)[:10], "reglas": reglas_a_dict(reglas), "version": ctx.version}, ""

    for seccion in SECCIONES:
        seccion.registrar(app, ctx)
    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=8050)
    args = parser.parse_args()
    crear_app().run(debug=False, port=args.puerto)


if __name__ == "__main__":
    main()
