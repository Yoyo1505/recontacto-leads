"""Seccion EVIDENCIA: que sabemos y con cuanta confianza.

Que muestra
    1. Tasa de "no contesta" por hora, espera, canal o dia, con intervalos de confianza.
    2. Mapa de espera contra hora: muestra que ambas variables van juntas (confusion).
    3. Que variables aportan al modelo (AUC por grupos de variables).
    4. Calibracion del modelo en el periodo de prueba.
    5. Control estadistico: carta p diaria y grafico de embudo por asesor.

Donde cambiar cosas
    - Dimensiones del selector: constante `DIMENSIONES`.
    - Orden de las categorias: constante `ORDEN`.
    - Limites de control (3 sigmas, 95% y 99.8%): `recontacto/control.py`.
    - Cada grafica es una funcion `figura_*` independiente.
"""

import numpy as np
import plotly.graph_objects as go
from componentes import en_columnas, encabezado, fila_kpi, grafica, kpi, nota, tarjeta
from dash import Input, Output, dcc
from tema import COLORES, ESCALA_AZUL, estilo

from recontacto import config, control

ID = "evidencia"
TITULO = "Evidencia"
RUTA = "/evidencia"

DIMENSIONES = {
    "franja_hora": "Hora del contacto",
    "rango_espera": "Espera desde el registro",
    "canal": "Canal",
    "dia_semana": "Día de la semana",
}
ORDEN = {
    "franja_hora": ["<9", "9-10", "11-12", "13-15", "16-18", "19+"],
    "rango_espera": ["<30min", "30min-2h", "2-6h", "6-12h", "12-24h", ">24h"],
    "dia_semana": list(config.DIAS_SEMANA),
}
NOMBRES_ABLACION = {
    "solo_canal": "Solo canal",
    "horario_y_canal": "Horario y canal",
    "solo_espera": "Solo espera",
    "solo_horario": "Solo horario",
    "espera_y_horario": "Espera y horario",
    "perfil": "Perfil (objetivo, edad, plan)",
    "todo": "Todas las variables",
}


def figura_tasas(X, y, dimension):
    t = control.tasas_por(X, y, dimension)
    if dimension in ORDEN:
        t = t.set_index(dimension).reindex([c for c in ORDEN[dimension] if c in set(t[dimension])]).reset_index()
    else:
        t = t.sort_values("tasa")
    media = float(1 - y.mean())
    fig = go.Figure(
        go.Bar(
            x=t[dimension],
            y=t["tasa"] * 100,
            marker_color=COLORES["primario"],
            error_y=dict(
                type="data",
                symmetric=False,
                array=(t["alto"] - t["tasa"]) * 100,
                arrayminus=(t["tasa"] - t["bajo"]) * 100,
                color=COLORES["suave"],
            ),
            customdata=np.stack([t["n"], t["bajo"] * 100, t["alto"] * 100], axis=-1),
            hovertemplate="%{x}: %{y:.1f}%<br>n = %{customdata[0]}<br>Intervalo 95%: %{customdata[1]:.0f}% a %{customdata[2]:.0f}%<extra></extra>",
        )
    )
    fig.add_hline(y=media * 100, line_dash="dash", line_color=COLORES["alerta"], annotation_text=f"Promedio {media:.0%}", annotation_position="top left")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title="% que no contesta", range=[0, 85])
    return estilo(fig, alto=360, leyenda=False)


def figura_confusion(X, y, minimo=10):
    tabla = X.assign(no_contesta=1 - y.to_numpy())
    filas, columnas = ORDEN["franja_hora"], ORDEN["rango_espera"]
    z = np.full((len(filas), len(columnas)), np.nan)
    n = np.zeros((len(filas), len(columnas)), dtype=int)
    for i, f in enumerate(filas):
        for j, c in enumerate(columnas):
            celda = tabla[(tabla["franja_hora"] == f) & (tabla["rango_espera"] == c)]
            n[i, j] = len(celda)
            if len(celda) >= minimo:
                z[i, j] = celda["no_contesta"].mean() * 100
    texto = [[f"n={n[i, j]}" if n[i, j] else "" for j in range(len(columnas))] for i in range(len(filas))]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=columnas,
            y=filas,
            text=texto,
            texttemplate="%{text}",
            colorscale=ESCALA_AZUL,
            zmin=20,
            zmax=70,
            hovertemplate="Hora %{y}, espera %{x}<br>No contesta: %{z:.0f}%<br>%{text}<extra></extra>",
            colorbar=dict(title="% no contesta"),
        )
    )
    fig.update_xaxes(title="Espera desde el registro", type="category")
    fig.update_yaxes(title="Hora del contacto", type="category", autorange="reversed")
    return estilo(fig, alto=360, leyenda=False)


def figura_ablacion(resultados):
    a = resultados["ablacion"]
    orden = sorted(a, key=a.get)
    fig = go.Figure(
        go.Bar(
            x=[a[k] for k in orden],
            y=[NOMBRES_ABLACION.get(k, k) for k in orden],
            orientation="h",
            marker_color=[COLORES["acento"] if k in ("solo_canal", "horario_y_canal") else COLORES["primario"] for k in orden],
            hovertemplate="%{y}: AUC %{x:.3f}<extra></extra>",
        )
    )
    fig.add_vline(x=0.5, line_dash="dash", line_color=COLORES["alerta"], annotation_text="Azar (0.5)")
    fig.update_xaxes(title="AUC en el periodo de prueba", range=[0.45, 0.65])
    return estilo(fig, alto=360, leyenda=False)


def figura_calibracion(resultados):
    c = resultados["calibracion_logistica"]
    pred = [f["predicha"] for f in c]
    obs = [f["observada"] for f in c]
    n = [f["n"] for f in c]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0.3, 0.9], y=[0.3, 0.9], mode="lines", line=dict(dash="dash", color=COLORES["suave"]), name="Calibración perfecta"))
    fig.add_trace(
        go.Scatter(
            x=pred,
            y=obs,
            mode="lines+markers",
            line=dict(color=COLORES["alerta"]),
            name="Modelo",
            customdata=n,
            hovertemplate="Predicha %{x:.0%}<br>Observada %{y:.0%}<br>n = %{customdata}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Probabilidad predicha de contestar", tickformat=".0%", range=[0.3, 0.9])
    fig.update_yaxes(title="Proporción observada", tickformat=".0%", range=[0.3, 0.9])
    return estilo(fig, alto=360)


def figura_carta_p(df):
    d = control.carta_p(df)
    fuera = d[d["fuera_de_control"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["limite_alto"] * 100, mode="lines", line=dict(color=COLORES["alerta"], dash="dot"), name="Límite superior (3σ)"))
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["limite_bajo"] * 100, mode="lines", line=dict(color=COLORES["alerta"], dash="dot"), name="Límite inferior (3σ)"))
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["centro"] * 100, mode="lines", line=dict(color=COLORES["suave"]), name="Promedio"))
    fig.add_trace(
        go.Scatter(
            x=d["fecha"],
            y=d["tasa"] * 100,
            mode="lines+markers",
            line=dict(color=COLORES["primario"]),
            name="% que no contesta",
            customdata=d["n"],
            hovertemplate="%{x|%d %b}: %{y:.0f}%<br>n = %{customdata}<extra></extra>",
        )
    )
    if len(fuera):
        fig.add_trace(go.Scatter(x=fuera["fecha"], y=fuera["tasa"] * 100, mode="markers", marker=dict(size=12, color=COLORES["alerta"], symbol="diamond"), name="Fuera de control"))
    fig.update_yaxes(title="% que no contesta", range=[0, 100])
    return estilo(fig, alto=360)


def figura_embudo_asesores(df):
    g, limites, centro = control.embudo(df)
    fig = go.Figure()
    for nombre, color in (("99.8%", COLORES["alerta"]), ("95%", COLORES["acento"])):
        for lado in ("alto", "bajo"):
            fig.add_trace(
                go.Scatter(
                    x=limites["n"],
                    y=limites[f"{lado}_{nombre}"] * 100,
                    mode="lines",
                    line=dict(color=color, dash="dot"),
                    name=f"Límite {nombre}",
                    showlegend=lado == "alto",
                    hoverinfo="skip",
                )
            )
    fig.add_hline(y=centro * 100, line_color=COLORES["suave"], annotation_text=f"Global {centro:.0%}")
    fig.add_trace(
        go.Scatter(
            x=g["n"],
            y=g["tasa"] * 100,
            mode="markers+text",
            text=g["asesor"],
            textposition="top center",
            marker=dict(size=12, color=[COLORES["alerta"] if f else COLORES["primario"] for f in g["fuera_de_control"]]),
            name="Asesores",
            hovertemplate="%{text}: %{y:.1f}%<br>contactos = %{x}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Contactos realizados")
    fig.update_yaxes(title="% que no contesta", range=[20, 60])
    return estilo(fig, alto=360)


def tarjetas_metricas(resultados):
    log = resultados["logistica"]
    bajo, alto = log["auc_ic95"]
    return fila_kpi(
        kpi("AUC del modelo", "kpi-auc", f"Intervalo 95%: {bajo:.2f} a {alto:.2f}", valor=f"{log['auc']:.2f}"),
        kpi("Azar", "kpi-azar", "AUC de la tasa constante", valor=f"{resultados['constante']['auc']:.2f}"),
        kpi("Precisión en el 10% más alto", "kpi-top", f"Base: {log['tasa_base']:.0%}", valor=f"{log['precision_top_decil']:.0%}"),
        kpi("Periodo de prueba", "kpi-prueba", f"{resultados['n_prueba']} contactos", valor=f"desde {resultados['corte'][8:10]}/{resultados['corte'][5:7]}"),
    )


def layout(ctx):
    resultados = ctx.evaluacion[0]
    return [
        encabezado("Evidencia", "Qué cambia la probabilidad de contestar y cuánta confianza merece cada hallazgo."),
        tarjetas_metricas(resultados),
        tarjeta(
            dcc.Dropdown(id="selector-dimension", options=[{"label": v, "value": k} for k, v in DIMENSIONES.items()], value="franja_hora", clearable=False, className="selector"),
            grafica("grafica-tasas", 360, figura_tasas(ctx.X, ctx.y, "franja_hora")),
            titulo="Dónde se pierde la respuesta",
            ayuda="Elige una variable. Las barras de error son intervalos de confianza al 95%: si dos barras se traslapan, la diferencia puede ser azar.",
        ),
        en_columnas(
            tarjeta(
                grafica("grafica-confusion", 360, figura_confusion(ctx.X, ctx.y)),
                titulo="La hora y la espera van juntas",
                ayuda="Los contactos de la tarde casi siempre fueron rápidos. Por eso no se puede separar el efecto de la hora del de la rapidez.",
            ),
            tarjeta(
                grafica("grafica-ablacion", 360, figura_ablacion(resultados)),
                titulo="Qué variables aportan",
                ayuda="El canal explica casi toda la señal; el perfil de la persona no aporta.",
            ),
        ),
        en_columnas(
            tarjeta(
                grafica("grafica-calibracion", 360, figura_calibracion(resultados)),
                titulo="Calibración",
                ayuda="Con puntos sobre la diagonal, la probabilidad predicha coincide con lo observado. Aquí el modelo subestima en los grupos bajos.",
            ),
            tarjeta(
                grafica("grafica-carta-p", 360, figura_carta_p(ctx.df)),
                titulo="Control estadístico por día",
                ayuda="Carta p: un día fuera de los límites sería una señal de algo distinto al azar.",
            ),
        ),
        tarjeta(
            grafica("grafica-embudo-asesores", 360, figura_embudo_asesores(ctx.df)),
            titulo="¿Algún asesor se aleja del promedio?",
            ayuda="Gráfico de embudo: los límites se cierran al crecer el número de contactos. Un punto dentro de los límites no se distingue del azar.",
        ),
        nota("Evaluación hacia adelante en el tiempo: se entrena con leads anteriores al corte y se prueba con los posteriores."),
    ]


def registrar(app, ctx):
    @app.callback(Output("grafica-tasas", "figure"), Input("selector-dimension", "value"))
    def cambiar_dimension(dimension):
        return figura_tasas(ctx.X, ctx.y, dimension)
