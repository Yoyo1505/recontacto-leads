"""Seccion DATOS: actualizar la informacion sin tocar codigo.

Que permite
    1. Subir un archivo (CSV, JSON, Excel o Parquet) con personas nuevas o con resultados
       actualizados. Se valida, se muestra un informe y la herramienta dice que haria con cada
       persona. Solo se guarda al pulsar "Aplicar cambios".
    2. Agregar una persona a mano (pasa por la misma validacion).
    3. Registrar una baja: quien pide no recibir mensajes se respeta siempre.
    4. Restaurar una version anterior de la base, o volver a la original.

Como fluye una persona nueva
    se valida -> se compara con la base por lead_id -> se le aplican las reglas de trato
    -> se le asigna horario y mensaje, o se explica por que hoy no se le escribe.

Donde cambiar cosas
    - Reglas de validacion y formatos aceptados: `recontacto/ingesta/validacion.py` y `esquema.py`.
    - Canales y opciones del formulario: constantes `CANALES`, `OBJETIVOS`, `PLANES`.
    - Tamano maximo de archivo: `LIMITE_MB`.
    - Para varias personas usando la app a la vez habria que guardar el estado pendiente por
      sesion; hoy es un solo usuario local (atributo `ctx.pendiente`).
"""

import base64
import re
from datetime import datetime, timedelta

import pandas as pd
from componentes import encabezado, fila_kpi, kpi, nota, tarjeta
from contexto import estado_inicial
from dash import Input, Output, State, dcc, html, no_update
from dash import ctx as contexto_dash

from recontacto import ingesta

from .lista import etiqueta_horario

ID = "datos"
TITULO = "Datos"
RUTA = "/datos"

CANALES = ["Meta", "Google", "TikTok", "Referido", "Organico", "Agente IA"]
OBJETIVOS = ["control de peso", "diabetes tipo 2"]
PLANES = [1299, 1599, 2499]
LIMITE_MB = 20


def tabla_html(df, columnas, maximo=12):
    if df is None or len(df) == 0:
        return html.P("Sin filas.", className="ayuda")
    cabecera = html.Tr([html.Th(c) for c in columnas])
    cuerpo = [html.Tr([html.Td("" if pd.isna(f[c]) else str(f[c])) for c in columnas]) for _, f in df.head(maximo).iterrows()]
    extra = [html.P(f"Se muestran {maximo} de {len(df)} filas.", className="ayuda")] if len(df) > maximo else []
    return html.Div([html.Table([html.Thead(cabecera), html.Tbody(cuerpo)], className="tabla-simple"), *extra])


def bloque_decisiones(decisiones):
    if decisiones is None or len(decisiones) == 0:
        return html.P("No hay personas nuevas ni actualizadas que mostrar.", className="ayuda")
    mostrar = decisiones.copy()
    mostrar["horario"] = mostrar["horario"].map(lambda h: "" if pd.isna(h) else etiqueta_horario(pd.Timestamp(h)))
    return tabla_html(mostrar, ["lead_id", "decision", "horario", "motivo", "mensaje"], maximo=10)


def bloque_informe(informe, decisiones=None):
    hijos = [html.Pre(informe.texto(), className="informe")]
    if len(informe.rechazados):
        columnas = [c for c in ("lead_id", "motivo") if c in informe.rechazados.columns]
        hijos.append(html.H4("Filas rechazadas (no se guardan; revisa y vuelve a subirlas)"))
        hijos.append(tabla_html(informe.rechazados, columnas))
    if decisiones is not None:
        hijos.append(html.H4("Qué haría la herramienta con estas personas"))
        hijos.append(bloque_decisiones(decisiones))
    return hijos


def siguiente_id(ctx):
    numeros = [int(m.group(1)) for i in ctx.df["lead_id"] for m in [re.fullmatch(r"L(\d+)", i)] if m]
    return f"L{(max(numeros) if numeros else 0) + 1:05d}"


def resumen_base(ctx):
    inicio, fin = ctx.df["fecha_registro"].min(), ctx.df["fecha_registro"].max()
    return [
        f"{len(ctx.df):,}",
        f"{inicio:%d/%m} a {fin:%d/%m/%Y}",
        f"{ctx.n_bajas:,}",
        ctx.ruta.name,
    ]


def layout(ctx):
    valores = resumen_base(ctx)
    ayer = (ctx.fecha_inicial - timedelta(days=1)).strftime("%Y-%m-%d")
    return [
        encabezado("Datos", "Actualiza la información sin tocar código: sube un archivo o agrega personas. Nada se guarda hasta que lo confirmas."),
        fila_kpi(
            kpi("Leads en la base", "kpi-datos-leads", valor=valores[0]),
            kpi("Periodo", "kpi-datos-periodo", valor=valores[1]),
            kpi("Bajas registradas", "kpi-datos-bajas", "Nunca se les escribe", valor=valores[2]),
            kpi("Archivo activo", "kpi-datos-archivo", valor=valores[3]),
        ),
        tarjeta(
            dcc.Upload(
                id="datos-subir",
                children=html.Div(["Arrastra un archivo o ", html.A("elige uno"), " (CSV, JSON, Excel o Parquet)"]),
                accept=".csv,.json,.jsonl,.xlsx,.xls,.parquet",
                max_size=LIMITE_MB * 1024 * 1024,
                className="zona-subida",
            ),
            html.P(
                "Se aceptan sinónimos de columnas (por ejemplo celular o whatsapp en lugar de telefono). "
                "Obligatorias: lead_id, fecha_registro, canal, telefono y resultado. Para bases de datos y nube usa los archivos .bat (ver docs).",
                className="ayuda",
            ),
            titulo="1. Subir información",
        ),
        tarjeta(
            html.Div(
                [
                    html.Div([html.Label("Canal"), dcc.Dropdown(id="form-canal", options=CANALES, value="Agente IA", clearable=False)]),
                    html.Div([html.Label("Objetivo"), dcc.Dropdown(id="form-objetivo", options=OBJETIVOS, value=OBJETIVOS[0], clearable=False)]),
                    html.Div([html.Label("Plan de interés"), dcc.Dropdown(id="form-plan", options=PLANES, value=PLANES[1], clearable=False)]),
                    html.Div([html.Label("Edad"), dcc.Input(id="form-edad", type="number", min=18, max=100, value=38, className="entrada")]),
                    html.Div([html.Label("Teléfono"), dcc.Input(id="form-telefono", type="text", placeholder="55-12345678", className="entrada")]),
                    html.Div([html.Label("Entidad"), dcc.Input(id="form-entidad", type="text", value="CDMX", className="entrada")]),
                    html.Div([html.Label("Fecha y hora de registro"), dcc.Input(id="form-fecha", type="text", value=f"{ayer} 20:00", className="entrada")]),
                    html.Div(
                        [
                            html.Label("¿Ya se intentó contactar?"),
                            dcc.Dropdown(id="form-resultado", options=[{"label": "No, nunca", "value": "sin_contactar"}, {"label": "Sí, no contestó", "value": "no_contesta"}], value="sin_contactar", clearable=False),
                        ]
                    ),
                    html.Div([html.Label("Fecha y hora del intento"), dcc.Input(id="form-contacto", type="text", placeholder="AAAA-MM-DD HH:MM", className="entrada")]),
                ],
                className="formulario",
            ),
            html.Button("Revisar persona", id="form-revisar", className="boton boton-claro"),
            titulo="2. O agrega una persona",
            ayuda="Pasa por la misma validación y muestra qué haría la herramienta con ella.",
        ),
        tarjeta(
            html.Div(id="datos-informe", children=html.P("Aquí aparecerá el informe.", className="ayuda")),
            html.Button("Aplicar cambios", id="datos-aplicar", n_clicks=0, disabled=True, className="boton"),
            html.Div(id="datos-mensaje-aplicar", className="mensaje-accion"),
            titulo="Informe y confirmación",
        ),
        tarjeta(
            html.Div(
                [
                    dcc.Input(id="baja-telefono", type="text", placeholder="Teléfono de quien pidió no recibir mensajes", className="entrada"),
                    html.Button("Registrar baja", id="baja-boton", className="boton"),
                ],
                className="fila-accion",
            ),
            html.Div(id="baja-mensaje", className="mensaje-accion"),
            titulo="3. Respetar a quien pide no recibir mensajes",
            ayuda="Se guarda en data/bajas.csv y se aplica a toda la base, incluso si el mismo teléfono aparece en archivos futuros.",
        ),
        tarjeta(
            html.Div(
                [
                    dcc.Dropdown(id="version-lista", options=[], placeholder="Elige una versión anterior", className="selector-ancho"),
                    html.Button("Restaurar versión", id="version-restaurar", className="boton boton-claro"),
                    html.Button("Volver a la base original", id="version-original", className="boton boton-claro"),
                ],
                className="fila-accion",
            ),
            html.Div(id="version-mensaje", className="mensaje-accion"),
            titulo="4. Volver atrás",
            ayuda="Cada cambio guarda una copia de la versión anterior; restaurar también guarda la actual, así que nada se pierde.",
        ),
        nota("Para actualizar desde una base de datos o la nube, usa bat/actualizar_desde_base.bat y bat/actualizar_desde_nube.bat."),
    ]


def _crudo_formulario(ctx, canal, objetivo, plan, edad, telefono, entidad, fecha, resultado, contacto):
    return pd.DataFrame(
        [
            {
                "lead_id": siguiente_id(ctx),
                "fecha_registro": fecha or "",
                "canal": canal or "",
                "anuncio": "",
                "estado": entidad or "",
                "edad": "" if edad is None else str(edad),
                "objetivo": objetivo or "",
                "plan_de_interes": "" if plan is None else str(plan),
                "telefono": telefono or "",
                "asesor": "",
                "primer_contacto": contacto or "",
                "resultado": resultado or "sin_contactar",
                "monto_venta": "",
            }
        ]
    )


def _estado_nuevo(ctx, estado):
    return estado_inicial(ctx, estado["reglas"] if estado else None)


def registrar(app, ctx):
    @app.callback(
        Output("datos-informe", "children"),
        Output("datos-aplicar", "disabled"),
        Output("datos-mensaje-aplicar", "children", allow_duplicate=True),
        Input("datos-subir", "contents"),
        Input("form-revisar", "n_clicks"),
        State("datos-subir", "filename"),
        State("form-canal", "value"),
        State("form-objetivo", "value"),
        State("form-plan", "value"),
        State("form-edad", "value"),
        State("form-telefono", "value"),
        State("form-entidad", "value"),
        State("form-fecha", "value"),
        State("form-resultado", "value"),
        State("form-contacto", "value"),
        prevent_initial_call=True,
    )
    def revisar(contenido, _clics, nombre, canal, objetivo, plan, edad, telefono, entidad, fecha, resultado, contacto):
        try:
            if contexto_dash.triggered_id == "datos-subir":
                if not contenido:
                    return no_cambio()
                datos = base64.b64decode(contenido.split(",", 1)[1])
                crudo, origen = ingesta.leer_bytes(nombre, datos), nombre
            elif not _clics:
                return no_cambio()
            else:
                crudo = _crudo_formulario(ctx, canal, objetivo, plan, edad, telefono, entidad, fecha, resultado, contacto)
                origen = "formulario"
            informe = ingesta.procesar(crudo, origen, base=ingesta.leer_canonico(ctx.ruta))
        except ingesta.ErrorIngesta as error:
            ctx.pendiente = None
            return html.Pre(f"Error: {error}", className="informe error-informe"), True, ""
        ctx.pendiente = informe
        decisiones = None
        if informe.hay_cambios and len(informe.agregados) + len(informe.actualizados) <= 200:
            decisiones = ingesta.simular_llegada(informe, hoy=datetime.combine(ctx.fecha_inicial, datetime.min.time()).replace(hour=8))
        return bloque_informe(informe, decisiones), not informe.hay_cambios, ""

    def no_cambio():
        return no_update, no_update, no_update

    @app.callback(
        Output("datos-mensaje-aplicar", "children"),
        Output("datos-aplicar", "disabled", allow_duplicate=True),
        Output("estado", "data", allow_duplicate=True),
        Output("ctl-fecha", "date", allow_duplicate=True),
        Input("datos-aplicar", "n_clicks"),
        State("estado", "data"),
        prevent_initial_call=True,
    )
    def aplicar(clics, estado):
        informe = ctx.pendiente
        if not clics or informe is None:
            return "", True, no_update, no_update
        ingesta.aplicar(informe)
        ctx.ids_nuevos = list(informe.agregados) + list(informe.actualizados)
        ctx.pendiente = None
        ctx.recargar()
        nuevo = _estado_nuevo(ctx, estado)
        lista, excluidos = ctx.lista(nuevo)
        decisiones = ingesta.decisiones_para(ctx.ids_nuevos, lista, excluidos)
        return (
            html.Div(
                [
                    html.P(f"Listo: {len(informe.agregados)} nuevas, {len(informe.actualizados)} actualizadas. La lista ya las incluye.", className="exito"),
                    bloque_decisiones(decisiones),
                ]
            ),
            True,
            nuevo,
            nuevo["fecha"],
        )

    @app.callback(
        Output("baja-mensaje", "children"),
        Output("estado", "data", allow_duplicate=True),
        Output("ctl-fecha", "date", allow_duplicate=True),
        Input("baja-boton", "n_clicks"),
        State("baja-telefono", "value"),
        State("estado", "data"),
        prevent_initial_call=True,
    )
    def registrar_baja(clics, telefono, estado):
        if not clics:
            return no_update, no_update, no_update
        try:
            nueva = ingesta.agregar_baja(telefono or "")
        except ingesta.ErrorIngesta as error:
            return html.Span(f"Error: {error}", className="error"), no_update, no_update
        if not nueva:
            return "Ese teléfono ya estaba en la lista de bajas.", no_update, no_update
        ctx.recargar()
        nuevo = _estado_nuevo(ctx, estado)
        return html.Span("Baja registrada: no se le volverá a escribir.", className="exito"), nuevo, nuevo["fecha"]

    @app.callback(
        Output("version-mensaje", "children"),
        Output("estado", "data", allow_duplicate=True),
        Output("ctl-fecha", "date", allow_duplicate=True),
        Input("version-restaurar", "n_clicks"),
        Input("version-original", "n_clicks"),
        State("version-lista", "value"),
        State("estado", "data"),
        prevent_initial_call=True,
    )
    def restaurar(clics_version, clics_original, version, estado):
        if not (clics_version or clics_original):
            return no_update, no_update, no_update
        try:
            if contexto_dash.triggered_id == "version-original":
                elegida = ingesta.restaurar("original")
            elif version:
                elegida = ingesta.restaurar(version)
            else:
                return "Elige una versión de la lista.", no_update, no_update
        except ingesta.ErrorIngesta as error:
            return html.Span(f"Error: {error}", className="error"), no_update, no_update
        ctx.recargar()
        nuevo = _estado_nuevo(ctx, estado)
        return html.Span(f"Base restaurada a: {elegida}", className="exito"), nuevo, nuevo["fecha"]

    @app.callback(
        Output("kpi-datos-leads", "children"),
        Output("kpi-datos-periodo", "children"),
        Output("kpi-datos-bajas", "children"),
        Output("kpi-datos-archivo", "children"),
        Output("version-lista", "options"),
        Input("estado", "data"),
    )
    def refrescar(_):
        return (*resumen_base(ctx), list(reversed(ingesta.listar_versiones())))
