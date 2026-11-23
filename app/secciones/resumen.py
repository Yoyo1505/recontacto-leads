"""Seccion RESUMEN: la historia en una pantalla.

Que muestra
    - Cuatro cifras de la lista del dia (dependen de las reglas de la barra lateral).
    - El embudo completo: de quien pidio informacion a quien compro.
    - Cuanto cambia el "no contesta" segun el canal, con su intervalo de confianza.

Donde cambiar cosas
    - Texto de portada: constante `PORTADA`.
    - Etapas del embudo: funcion `figura_embudo`.
    - Cifras de arriba: funcion `calcular_kpis`.
    - Para quitar o agregar una grafica: edita `layout` y, si es dinamica, `registrar`.
"""

import plotly.graph_objects as go
from componentes import en_columnas, encabezado, fila_kpi, grafica, kpi, nota, tarjeta
from dash import Input, Output
from tema import COLORES, estilo

from recontacto import control

ID = "resumen"
TITULO = "Resumen"
RUTA = "/"

PORTADA = (
    "Cuatro de cada diez personas que pidieron información no contestan cuando un asesor las busca. "
    "Esta herramienta arma cada mañana la lista de a quién volver a buscar, cuándo y con qué mensaje, "
    "sin dejar de lado a nadie."
)


def figura_embudo(df):
    unicos = df[~df["es_duplicado"]]
    contactados = unicos[unicos["primer_contacto"].notna()]
    contestaron = contactados[contactados["resultado"] != "no_contesta"]
    compraron = contestaron[contestaron["resultado"] == "venta"]
    etapas = ["Pidieron información", "Recibieron un contacto", "Contestaron", "Compraron"]
    valores = [len(unicos), len(contactados), len(contestaron), len(compraron)]
    fig = go.Figure(
        go.Funnel(
            y=etapas,
            x=valores,
            textinfo="value+percent previous",
            marker=dict(color=[COLORES["oscuro"], COLORES["primario"], COLORES["secundario"], COLORES["acento"]]),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    estilo(fig, alto=340, leyenda=False)
    fig.update_layout(margin=dict(l=170, r=16, t=16, b=44))
    return fig


def figura_no_contesta_canal(df):
    t = control.tabla_con_intervalos(df, "canal").sort_values("tasa")
    fig = go.Figure(
        go.Bar(
            x=t["tasa"] * 100,
            y=t["canal"],
            orientation="h",
            marker_color=COLORES["primario"],
            error_x=dict(
                type="data",
                symmetric=False,
                array=(t["alto"] - t["tasa"]) * 100,
                arrayminus=(t["tasa"] - t["bajo"]) * 100,
                color=COLORES["suave"],
            ),
            customdata=t[["n", "bajo", "alto"]].to_numpy(),
            hovertemplate="%{y}: %{x:.1f}%<br>n = %{customdata[0]}<br>Intervalo 95%%: %{customdata[1]:.1%} a %{customdata[2]:.1%}<extra></extra>",
        )
    )
    fig.update_xaxes(title="% que no contesta", range=[0, 70])
    return estilo(fig, alto=340, leyenda=False)


def calcular_kpis(lista, excluidos):
    asignados = lista[lista["accion"] == "contactar"]
    prob = asignados["prob_asignada"].mean() if len(asignados) else 0.0
    return [
        f"{len(lista):,}",
        f"{int(lista['nunca_contactado'].sum()):,}",
        f"{prob:.0%}",
        f"{len(excluidos):,}",
    ]


def layout(ctx):
    return [
        encabezado("Que nadie se quede esperando", PORTADA),
        fila_kpi(
            kpi("Personas por recontactar", "kpi-resumen-leads", "Con las reglas de la barra lateral"),
            kpi("Nunca contactadas", "kpi-resumen-nuevos", "Salen primero y el mismo día"),
            kpi("Probabilidad media de contestar", "kpi-resumen-prob", "En el horario asignado"),
            kpi("Registros fuera de la lista", "kpi-resumen-excluidos", "Ya resueltos, en conversación o fuera de ventana"),
        ),
        en_columnas(
            tarjeta(
                grafica("grafica-embudo", 340, figura_embudo(ctx.df)),
                titulo="Del interés a la compra",
                ayuda="Cada barra muestra cuántas personas llegan a la siguiente etapa.",
            ),
            tarjeta(
                grafica("grafica-canal", 340, figura_no_contesta_canal(ctx.df)),
                titulo="Quién no contesta, por canal",
                ayuda="Las barras de error son el intervalo de confianza al 95%.",
            ),
        ),
        nota(
            "Los datos son ficticios (1,811 registros del 28-sep al 08-nov-2026). "
            "Las reglas de trato y los supuestos están documentados en docs/README.md."
        ),
    ]


def registrar(app, ctx):
    @app.callback(
        Output("kpi-resumen-leads", "children"),
        Output("kpi-resumen-nuevos", "children"),
        Output("kpi-resumen-prob", "children"),
        Output("kpi-resumen-excluidos", "children"),
        Input("estado", "data"),
    )
    def actualizar(estado):
        lista, excluidos = ctx.lista(estado)
        return calcular_kpis(lista, excluidos)
