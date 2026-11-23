"""Seccion LISTA DEL DIA: a quien contactar, cuando y con que mensaje.

Que muestra
    - Tabla ordenable y filtrable con la prioridad, el canal y el horario asignado.
    - Mapa de calor de contactos por dia y hora, para ver que la carga esta repartida.
    - Detalle de la persona elegida: por que se le asigno ese horario y el mensaje sugerido.
    - Descarga de la lista en CSV.

Donde cambiar cosas
    - Columnas de la tabla: `COLUMNAS_TABLA` y `filas_tabla`.
    - Filtros: `layout` (componentes) y `actualizar` (logica).
    - Mapa de calor: `figura_mapa_calor`.
    - Texto del detalle: `detalle`.
"""

import plotly.graph_objects as go
from componentes import en_columnas, encabezado, fila_kpi, grafica, kpi, tarjeta
from dash import Input, Output, State, dash_table, dcc, html
from tema import COLORES, ESCALA_AZUL, estilo

ID = "lista"
TITULO = "Lista del día"
RUTA = "/lista"

DIAS_CORTOS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
COLUMNAS_TABLA = [
    {"name": "Prioridad", "id": "prioridad", "type": "numeric"},
    {"name": "Lead", "id": "lead_id"},
    {"name": "Canal", "id": "canal"},
    {"name": "Acción", "id": "accion"},
    {"name": "Intento", "id": "intento", "type": "numeric"},
    {"name": "Horario asignado", "id": "horario"},
    {"name": "Prob. de contestar (%)", "id": "prob", "type": "numeric", "format": {"specifier": ".0f"}},
    {"name": "Asesor", "id": "asesor"},
]


def etiqueta_horario(momento):
    if momento is None or str(momento) == "NaT":
        return "sin horario"
    return f"{DIAS_CORTOS[momento.weekday()]} {momento.day:02d}/{momento.month:02d} {momento.hour:02d}:00"


def filas_tabla(lista):
    filas = []
    for _, f in lista.iterrows():
        filas.append(
            {
                "prioridad": int(f["prioridad"]),
                "lead_id": f["lead_id"],
                "canal": f["canal"],
                "accion": f["accion"],
                "intento": int(f["intento"]),
                "horario": etiqueta_horario(f["horario_asignado"]),
                "prob": None if f["prob_asignada"] != f["prob_asignada"] else round(float(f["prob_asignada"]) * 100, 1),
                "asesor": "" if f["asesor"] != f["asesor"] else f["asesor"],
                "motivo": f["motivo"],
                "mensaje": f["mensaje"],
                "origen": f["origen_mensaje"],
            }
        )
    return filas


def filtrar(lista, canales, solo_nuevos):
    vista = lista[lista["canal"].isin(canales)] if canales else lista.iloc[0:0]
    if solo_nuevos:
        vista = vista[vista["nunca_contactado"]]
    return vista


def figura_mapa_calor(lista):
    asignados = lista[lista["accion"] == "contactar"]
    fig = go.Figure()
    if len(asignados):
        base = asignados.assign(dia=asignados["horario_asignado"].dt.normalize(), hora=asignados["horario_asignado"].dt.hour)
        tabla = base.pivot_table(index="dia", columns="hora", values="lead_id", aggfunc="count", fill_value=0)
        tabla = tabla.sort_index(axis=1)
        etiquetas = [etiqueta_horario(d).rsplit(" ", 1)[0] for d in tabla.index]
        fig.add_trace(
            go.Heatmap(
                z=tabla.to_numpy(),
                x=[f"{h:02d}:00" for h in tabla.columns],
                y=etiquetas,
                colorscale=ESCALA_AZUL,
                hovertemplate="%{y} a las %{x}: %{z} contactos<extra></extra>",
                colorbar=dict(title="Contactos"),
            )
        )
        fig.update_yaxes(autorange="reversed")
    return estilo(fig, alto=300, leyenda=False)


def detalle(fila):
    if not fila:
        return html.P("Elige una fila de la tabla para ver el motivo y el mensaje.", className="ayuda")
    bloques = [html.H4(f"{fila['lead_id']} · {fila['canal']}"), html.P(fila["motivo"])]
    if fila.get("mensaje"):
        bloques.extend(
            [
                html.Div("Mensaje sugerido", className="etiqueta"),
                html.Div(fila["mensaje"], className="mensaje"),
                html.Div(f"Origen: {fila['origen']}", className="ayuda"),
            ]
        )
    return bloques


def layout(ctx):
    canales = sorted(ctx.df["canal"].unique())
    return [
        encabezado("Lista del día", "Quién, cuándo y con qué mensaje. Cambia las reglas en la barra lateral y la lista se recalcula."),
        fila_kpi(
            kpi("En la lista", "kpi-lista-total"),
            kpi("Con horario", "kpi-lista-asignados"),
            kpi("En cola", "kpi-lista-cola", "Se reprograman, no se descartan"),
        ),
        tarjeta(
            html.Div(
                [
                    dcc.Checklist(id="filtro-canales", options=canales, value=canales, inline=True, className="checks"),
                    dcc.Checklist(
                        id="filtro-nuevos",
                        options=[{"label": "Solo nunca contactadas", "value": "si"}],
                        value=[],
                        inline=True,
                        className="checks",
                    ),
                    html.Button("Descargar CSV", id="boton-descarga", className="boton"),
                    dcc.Download(id="descarga-lista"),
                ],
                className="barra-filtros",
            ),
            dash_table.DataTable(
                id="tabla-lista",
                columns=COLUMNAS_TABLA,
                data=[],
                page_size=12,
                sort_action="native",
                filter_action="native",
                row_selectable="single",
                style_header={"backgroundColor": COLORES["claro"], "color": COLORES["oscuro"], "fontWeight": "700", "border": "none"},
                style_cell={"fontFamily": "Inter, sans-serif", "fontSize": "13px", "padding": "8px", "border": "none", "borderBottom": f"1px solid {COLORES['linea']}"},
                style_data_conditional=[
                    {"if": {"filter_query": "{accion} = en_cola"}, "color": COLORES["alerta"]},
                    {"if": {"state": "selected"}, "backgroundColor": COLORES["claro"], "border": f"1px solid {COLORES['primario']}"},
                ],
            ),
        ),
        en_columnas(
            tarjeta(grafica("grafica-mapa-calor", 300), titulo="Carga por día y hora", ayuda="Cuántos contactos caen en cada hora. El límite por hora evita saturar al equipo."),
            tarjeta(html.Div(id="detalle-lead", children=detalle(None)), titulo="Detalle de la persona"),
        ),
    ]


def registrar(app, ctx):
    @app.callback(
        Output("tabla-lista", "data"),
        Output("grafica-mapa-calor", "figure"),
        Output("kpi-lista-total", "children"),
        Output("kpi-lista-asignados", "children"),
        Output("kpi-lista-cola", "children"),
        Input("estado", "data"),
        Input("filtro-canales", "value"),
        Input("filtro-nuevos", "value"),
    )
    def actualizar(estado, canales, nuevos):
        lista, _ = ctx.lista(estado)
        vista = filtrar(lista, canales or [], bool(nuevos))
        asignados = int((lista["accion"] == "contactar").sum())
        return (
            filas_tabla(vista),
            figura_mapa_calor(lista),
            f"{len(lista):,}",
            f"{asignados:,}",
            f"{len(lista) - asignados:,}",
        )

    @app.callback(
        Output("detalle-lead", "children"),
        Input("tabla-lista", "derived_virtual_selected_rows"),
        State("tabla-lista", "derived_virtual_data"),
    )
    def mostrar_detalle(seleccion, datos):
        if not seleccion or not datos:
            return detalle(None)
        return detalle(datos[seleccion[0]])

    @app.callback(
        Output("descarga-lista", "data"),
        Input("boton-descarga", "n_clicks"),
        State("estado", "data"),
        prevent_initial_call=True,
    )
    def descargar(_, estado):
        lista, _ = ctx.lista(estado)
        return dcc.send_data_frame(lista.to_csv, f"lista_{estado['fecha']}.csv", index=False, encoding="utf-8-sig")
