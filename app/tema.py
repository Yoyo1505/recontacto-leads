"""Identidad visual de la aplicacion: colores, tipografia y plantilla de Plotly.

Donde cambiar cosas
    - Colores: diccionario `COLORES`. Los mismos valores estan en `assets/estilo.css`
      (variables `--primario`, `--secundario`, etc.).
    - Estilo de todas las graficas: funcion `estilo`.
    - Secuencia de colores de las series: `SECUENCIA`.
"""

import plotly.graph_objects as go
import plotly.io as pio

COLORES = {
    "primario": "#00547C",
    "secundario": "#006A9C",
    "oscuro": "#002D42",
    "tinta": "#0B1F2C",
    "claro": "#E6F1F7",
    "gris": "#F4F5F5",
    "acento": "#00A99D",
    "alerta": "#C55A11",
    "suave": "#5B6B75",
    "linea": "#D5DEE4",
}
SECUENCIA = [COLORES["primario"], COLORES["acento"], COLORES["alerta"], "#7A8FA0", COLORES["secundario"], COLORES["oscuro"]]
ESCALA_AZUL = [[0, "#FFFFFF"], [0.5, "#7FB2CB"], [1, COLORES["oscuro"]]]
FUENTE = "Inter, system-ui, -apple-system, Segoe UI, sans-serif"

_PLANTILLA = go.layout.Template(
    layout=dict(
        font=dict(family=FUENTE, color=COLORES["tinta"], size=13),
        colorway=SECUENCIA,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=COLORES["linea"], zerolinecolor=COLORES["linea"], linecolor=COLORES["linea"]),
        yaxis=dict(gridcolor=COLORES["linea"], zerolinecolor=COLORES["linea"], linecolor=COLORES["linea"]),
        hoverlabel=dict(font=dict(family=FUENTE)),
    )
)
pio.templates["clivi"] = _PLANTILLA
pio.templates.default = "clivi"


def estilo(fig, titulo=None, alto=360, leyenda=True):
    """Aplica el estilo comun a cualquier figura."""
    fig.update_layout(
        template="clivi",
        title=dict(text=titulo, x=0, font=dict(size=15, color=COLORES["oscuro"])) if titulo else None,
        height=alto,
        margin=dict(l=48, r=16, t=48 if titulo else 16, b=84 if leyenda else 44),
        showlegend=leyenda,
        legend=dict(orientation="h", y=-0.32, x=0),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig
