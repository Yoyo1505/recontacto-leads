"""Seccion SIMULACION: cuanto mejoraria el recontacto y con cuanta incertidumbre.

Que muestra
    - Histograma de la diferencia en personas que contestan (politica del modelo menos horario sin
      optimizar) en miles de corridas, con su intervalo de 95%.
    - Sensibilidad al supuesto `alpha`: que fraccion de la ventaja del horario es causal.
    - Tasas de respuesta simuladas por brazo.

Como leerla
    Cada corrida elige un modelo bootstrap al azar (incertidumbre del modelo) y sortea quien
    contesta (azar del muestreo). Si el intervalo cruza el cero, un dia de recontacto no basta para
    distinguir la mejora del azar: hace falta una prueba A/B (ver seccion Prueba A/B).

Donde cambiar cosas
    - Valores iniciales de los controles: constantes `ALPHA_INICIAL` y `SIMULACIONES_INICIAL`.
    - Logica de simulacion: `recontacto/simulacion.py`.
    - Graficas: funciones `figura_*`.
"""

import plotly.graph_objects as go
from componentes import en_columnas, encabezado, fila_kpi, grafica, kpi, nota, tarjeta
from dash import Input, Output, dcc, html
from tema import COLORES, estilo

from recontacto import simulacion as sim

ID = "simulacion"
TITULO = "Simulación"
RUTA = "/simulacion"

ALPHA_INICIAL = 0.5
SIMULACIONES_INICIAL = 2000


def figura_histograma(corridas, r):
    fig = go.Figure(
        go.Histogram(
            x=corridas["diferencia"],
            nbinsx=40,
            marker_color=COLORES["primario"],
            opacity=0.85,
            hovertemplate="Diferencia %{x}: %{y} corridas<extra></extra>",
        )
    )
    fig.add_vrect(x0=r["ic_bajo"], x1=r["ic_alto"], fillcolor=COLORES["acento"], opacity=0.12, line_width=0, annotation_text="IC 95%", annotation_position="top left")
    fig.add_vline(x=0, line_color=COLORES["alerta"], line_dash="dash", annotation_text="Sin mejora", annotation_position="top left")
    fig.add_vline(x=r["media"], line_color=COLORES["oscuro"], annotation_text=f"Media {r['media']:.1f}", annotation_position="top right")
    fig.update_xaxes(title="Personas adicionales que contestan (de la lista del día)")
    fig.update_yaxes(title="Corridas")
    return estilo(fig, alto=360, leyenda=False)


def figura_sensibilidad(tabla, alpha_actual):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tabla["alpha"], y=tabla["ic_alto"], mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(
        go.Scatter(x=tabla["alpha"], y=tabla["ic_bajo"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(0,169,157,0.18)", name="IC 95%", hoverinfo="skip")
    )
    fig.add_trace(
        go.Scatter(
            x=tabla["alpha"],
            y=tabla["media"],
            mode="lines+markers",
            line=dict(color=COLORES["primario"]),
            name="Mejora media",
            customdata=tabla["prob_mejora"],
            hovertemplate="alpha %{x:.1f}<br>Mejora media %{y:.1f} personas<br>Prob. de mejora %{customdata:.0%}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color=COLORES["alerta"])
    fig.add_vline(x=alpha_actual, line_color=COLORES["oscuro"], line_dash="dot", annotation_text="Tu supuesto")
    fig.update_xaxes(title="Parte de la ventaja del horario que es causal (alpha)", range=[0, 1])
    fig.update_yaxes(title="Personas adicionales que contestan")
    return estilo(fig, alto=360)


def figura_tasas(corridas):
    fig = go.Figure()
    fig.add_trace(go.Box(y=corridas["tasa_base"] * 100, name="Horario sin optimizar", marker_color=COLORES["suave"], boxmean=True))
    fig.add_trace(go.Box(y=corridas["tasa_politica"] * 100, name="Horario del modelo", marker_color=COLORES["primario"], boxmean=True))
    fig.update_yaxes(title="% que contesta en la lista")
    return estilo(fig, alto=360, leyenda=False)


def interpretar(r, alpha, n_leads):
    cruza = r["ic_bajo"] <= 0 <= r["ic_alto"]
    base = (
        f"Con alpha = {alpha:.2f}, el horario del modelo hace que contesten en promedio {r['media']:.1f} personas más "
        f"de {n_leads} (intervalo 95%: {r['ic_bajo']:.0f} a {r['ic_alto']:.0f}). "
        f"En {r['prob_mejora']:.0%} de las corridas el modelo supera al horario sin optimizar."
    )
    if cruza:
        return base + " El intervalo incluye el cero: con un solo día de lista no se puede distinguir la mejora del azar."
    return base + " El intervalo no incluye el cero: bajo este supuesto la mejora es distinguible del azar."


def layout(ctx):
    return [
        encabezado("Simulación", "Qué pasaría si recontactamos con los horarios del modelo, con la incertidumbre a la vista."),
        tarjeta(
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Parte de la ventaja del horario que es causal (alpha)"),
                            dcc.Slider(id="sim-alpha", min=0, max=1, step=0.05, value=ALPHA_INICIAL, marks={0: "0", 0.5: "0.5", 1: "1"}, tooltip={"placement": "bottom"}),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Número de simulaciones"),
                            dcc.Slider(id="sim-n", min=500, max=5000, step=500, value=SIMULACIONES_INICIAL, marks={500: "500", 2500: "2,500", 5000: "5,000"}, tooltip={"placement": "bottom"}),
                        ]
                    ),
                ],
                className="controles-dobles",
            ),
            html.P(
                "alpha = 0 significa que el horario no importa; alpha = 1, que toda la ventaja observada es causal. "
                "En los datos, el horario y la rapidez del contacto están mezclados, así que no se sabe cuál es el valor real.",
                className="ayuda",
            ),
        ),
        fila_kpi(
            kpi("Mejora media", "kpi-sim-media", "Personas adicionales que contestan"),
            kpi("Intervalo 95%", "kpi-sim-ic", "Incertidumbre total"),
            kpi("Probabilidad de mejora", "kpi-sim-prob", "Corridas en que gana el modelo"),
            kpi("Ventas extra esperadas", "kpi-sim-ventas", "Según la conversión histórica por canal"),
        ),
        tarjeta(html.Div(id="sim-texto", className="interpretacion")),
        en_columnas(
            tarjeta(grafica("grafica-sim-hist", 360), titulo="Distribución de la mejora"),
            tarjeta(grafica("grafica-sim-sens", 360), titulo="Sensibilidad al supuesto"),
        ),
        tarjeta(grafica("grafica-sim-tasas", 360), titulo="Tasa de respuesta simulada por brazo"),
        nota("Simulación con modelos bootstrap (100 remuestras) y Bernoulli por persona. El detalle del método está en el encabezado de recontacto/simulacion.py."),
    ]


def registrar(app, ctx):
    @app.callback(
        Output("kpi-sim-media", "children"),
        Output("kpi-sim-ic", "children"),
        Output("kpi-sim-prob", "children"),
        Output("kpi-sim-ventas", "children"),
        Output("sim-texto", "children"),
        Output("grafica-sim-hist", "figure"),
        Output("grafica-sim-sens", "figure"),
        Output("grafica-sim-tasas", "figure"),
        Input("estado", "data"),
        Input("sim-alpha", "value"),
        Input("sim-n", "value"),
    )
    def simular(estado, alpha, n_sim):
        prep = ctx.preparacion(estado)
        corridas = sim.simular(prep, alpha, int(n_sim), conversion=ctx.conversion)
        r = sim.resumen(corridas)
        sens = sim.sensibilidad_alpha(prep, n_sim=600, conversion=ctx.conversion)
        return (
            f"{r['media']:+.1f}",
            f"{r['ic_bajo']:.0f} a {r['ic_alto']:.0f}",
            f"{r['prob_mejora']:.0%}",
            f"{r['ventas_extra']:+.2f}",
            interpretar(r, alpha, prep.n_leads),
            figura_histograma(corridas, r),
            figura_sensibilidad(sens, alpha),
            figura_tasas(corridas),
        )
