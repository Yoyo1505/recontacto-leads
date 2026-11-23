"""Seccion PRUEBA A/B: cuanta gente y cuanto tiempo hacen falta para comprobar la mejora.

Que muestra
    - Personas necesarias por grupo y dias de prueba, segun el efecto que se quiere detectar.
    - Curvas de potencia: probabilidad de detectar un efecto segun el tamano de la prueba.
    - Tabla de tamanos de muestra por efecto y potencia.
    - Comprobacion del control del error tipo I (falsos positivos) por simulacion.

Como leerla
    Los efectos pequenos exigen muestras enormes. Con el flujo actual de leads, solo los efectos
    grandes se pueden comprobar en pocas semanas.

Donde cambiar cosas
    - Efectos a comparar en las curvas: constante `EFECTOS`.
    - Valores iniciales: constantes `EFECTO_INICIAL`, `ALFA_INICIAL`, `POTENCIA_INICIAL`.
    - Formulas: `recontacto/simulacion.py` (`tamano_muestra`, `potencia_analitica`).
"""

import numpy as np
import plotly.graph_objects as go
from componentes import en_columnas, encabezado, fila_kpi, grafica, kpi, nota, tarjeta
from dash import Input, Output, dcc, html
from tema import COLORES, estilo

from recontacto import simulacion as sim

ID = "ab"
TITULO = "Prueba A/B"
RUTA = "/ab"

EFECTOS = (0.02, 0.03, 0.05, 0.08, 0.10)
COLORES_EFECTOS = (COLORES['primario'], COLORES['acento'], COLORES['alerta'], '#7A8FA0', '#E0A526')
EFECTO_INICIAL = 3
ALFA_INICIAL = 0.05
POTENCIA_INICIAL = 0.8


def figura_potencia(p0, alfa, n_necesario):
    ns = np.unique(np.geomspace(50, 12000, 80).astype(int))
    fig = go.Figure()
    for i, delta in enumerate(EFECTOS):
        fig.add_trace(
            go.Scatter(
                x=ns,
                y=[sim.potencia_analitica(p0, delta, int(n), alfa) for n in ns],
                mode="lines",
                name=f"+{delta * 100:.0f} puntos",
                line=dict(color=COLORES_EFECTOS[i % len(COLORES_EFECTOS)]),
                hovertemplate="n = %{x} por grupo<br>Potencia %{y:.0%}<extra></extra>",
            )
        )
    fig.add_hline(y=0.8, line_dash="dash", line_color=COLORES["suave"], annotation_text="80%")
    fig.add_vline(x=n_necesario, line_dash="dot", line_color=COLORES["oscuro"], annotation_text="Tu escenario")
    fig.update_xaxes(title="Personas por grupo", type="log")
    fig.update_yaxes(title="Potencia", tickformat=".0%", range=[0, 1.02])
    return estilo(fig, alto=380)


def tabla_tamanos(p0, alfa, leads_por_dia):
    filas = []
    for delta in EFECTOS:
        fila = [f"+{delta * 100:.0f} puntos"]
        for potencia in (0.8, 0.9):
            n = sim.tamano_muestra(p0, delta, potencia, alfa)
            fila.append(f"{n:,} ({2 * n / leads_por_dia:,.0f} días)")
        filas.append(fila)
    return filas


def html_tabla(filas):
    cabecera = html.Tr([html.Th("Efecto a detectar"), html.Th("Potencia 80%"), html.Th("Potencia 90%")])
    cuerpo = [html.Tr([html.Td(c) for c in f]) for f in filas]
    return html.Table([html.Thead(cabecera), html.Tbody(cuerpo)], className="tabla-simple")


def layout(ctx):
    return [
        encabezado("Prueba A/B", "Cuánta gente y cuánto tiempo hacen falta para comprobar que la lista del modelo mejora el recontacto."),
        tarjeta(
            html.Div(
                [
                    html.Div([html.Label("Efecto a detectar (puntos porcentuales)"), dcc.Slider(id="ab-efecto", min=1, max=12, step=1, value=EFECTO_INICIAL, marks={1: "1", 3: "3", 6: "6", 12: "12"}, tooltip={"placement": "bottom"})]),
                    html.Div([html.Label("Nivel de significancia"), dcc.Dropdown(id="ab-alfa", options=[{"label": "5%", "value": 0.05}, {"label": "1%", "value": 0.01}], value=ALFA_INICIAL, clearable=False)]),
                    html.Div([html.Label("Potencia"), dcc.Dropdown(id="ab-potencia", options=[{"label": "80%", "value": 0.8}, {"label": "90%", "value": 0.9}], value=POTENCIA_INICIAL, clearable=False)]),
                    html.Div([html.Label("Leads nuevos por día"), dcc.Input(id="ab-flujo", type="number", min=1, max=1000, value=round(ctx.leads_por_dia), className="entrada")]),
                ],
                className="controles-cuatro",
            ),
            html.P(
                f"Tasa base de respuesta usada: {ctx.tasa_contesta:.0%} (la observada en los datos). El flujo por defecto es el promedio histórico de leads por día.",
                className="ayuda",
            ),
        ),
        fila_kpi(
            kpi("Personas por grupo", "kpi-ab-n"),
            kpi("Personas en total", "kpi-ab-total", "Dos grupos"),
            kpi("Duración estimada", "kpi-ab-dias", "Con el flujo indicado"),
            kpi("Falsos positivos simulados", "kpi-ab-falsos", "Debe quedar cerca del nivel elegido"),
        ),
        en_columnas(
            tarjeta(grafica("grafica-ab-potencia", 380), titulo="Potencia según el tamaño de la prueba"),
            tarjeta(html.Div(id="ab-tabla"), titulo="Tamaños de muestra por efecto", ayuda="Entre paréntesis, los días que tomaría con el flujo indicado."),
        ),
        nota("Prueba z de dos proporciones, de dos colas. La fórmula analítica se contrasta con una simulación en las pruebas automáticas."),
    ]


def registrar(app, ctx):
    @app.callback(
        Output("kpi-ab-n", "children"),
        Output("kpi-ab-total", "children"),
        Output("kpi-ab-dias", "children"),
        Output("kpi-ab-falsos", "children"),
        Output("grafica-ab-potencia", "figure"),
        Output("ab-tabla", "children"),
        Input("ab-efecto", "value"),
        Input("ab-alfa", "value"),
        Input("ab-potencia", "value"),
        Input("ab-flujo", "value"),
    )
    def calcular(efecto, alfa, potencia, flujo):
        p0 = ctx.tasa_contesta
        delta = efecto / 100
        flujo = max(float(flujo or 1), 1.0)
        n = sim.tamano_muestra(p0, delta, potencia, alfa)
        falsos = sim.potencia_simulada(p0, 0.0, n, sims=4000, alfa=alfa)
        return (
            f"{n:,}",
            f"{2 * n:,}",
            f"{2 * n / flujo:,.0f} días",
            f"{falsos:.1%}",
            figura_potencia(p0, alfa, n),
            html_tabla(tabla_tamanos(p0, alfa, flujo)),
        )
