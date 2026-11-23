"""Piezas de interfaz reutilizables por todas las secciones.

Donde cambiar cosas
    - Aspecto de tarjetas, KPIs y notas: `assets/estilo.css` (clases `.tarjeta`, `.kpi`, `.nota`).
    - Barra de herramientas de las graficas (descarga, zoom): `CONFIG_GRAFICA`.
"""

from dash import dcc, html

CONFIG_GRAFICA = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "scale": 3},
}


def encabezado(titulo, subtitulo=None):
    hijos = [html.H2(titulo)]
    if subtitulo:
        hijos.append(html.P(subtitulo, className="subtitulo"))
    return html.Div(hijos, className="encabezado-seccion")


def tarjeta(*hijos, titulo=None, ayuda=None, clase=""):
    contenido = []
    if titulo:
        contenido.append(html.H3(titulo))
    if ayuda:
        contenido.append(html.P(ayuda, className="ayuda"))
    contenido.extend(hijos)
    return html.Div(contenido, className=f"tarjeta {clase}".strip())


def kpi(titulo, id_valor, nota=None, valor="-"):
    hijos = [html.Div(titulo, className="kpi-titulo"), html.Div(valor, id=id_valor, className="kpi-valor")]
    if nota:
        hijos.append(html.Div(nota, className="kpi-nota"))
    return html.Div(hijos, className="kpi")


def fila_kpi(*kpis):
    return html.Div(list(kpis), className="fila-kpi")


def nota(texto):
    return html.P(texto, className="nota")


def grafica(id_grafica, alto=360, figura=None):
    return dcc.Graph(
        id=id_grafica,
        figure=figura if figura is not None else {},
        config=CONFIG_GRAFICA,
        style={"height": f"{alto}px"},
    )


def en_columnas(*hijos, proporcion="1fr 1fr"):
    return html.Div(list(hijos), className="columnas", style={"gridTemplateColumns": proporcion})
