import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from . import config, features
from .model import ModeloContacto

SEMILLA = 7


def dividir_en_el_tiempo(X, y, corte):
    mascara = X["fecha_registro"] < pd.Timestamp(corte)
    return X[mascara], y[mascara], X[~mascara], y[~mascara]


def metricas(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    tope = max(1, len(y) // 10)
    mejores = np.argsort(-p)[:tope]
    return {
        "n": int(len(y)),
        "tasa_base": float(y.mean()),
        "auc": float(roc_auc_score(y, p)) if len(set(y)) > 1 else float("nan"),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))),
        "precision_top_decil": float(y[mejores].mean()),
    }


def intervalo_auc(y, p, repeticiones=500):
    y = np.asarray(y)
    p = np.asarray(p)
    generador = np.random.default_rng(SEMILLA)
    valores = []
    for _ in range(repeticiones):
        muestra = generador.integers(0, len(y), len(y))
        if len(set(y[muestra])) > 1:
            valores.append(roc_auc_score(y[muestra], p[muestra]))
    return float(np.percentile(valores, 2.5)), float(np.percentile(valores, 97.5))


def calibracion(y, p, grupos=5):
    tabla = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    tabla["grupo"] = pd.qcut(tabla["p"], grupos, duplicates="drop")
    resumen = tabla.groupby("grupo", observed=True).agg(predicha=("p", "mean"), observada=("y", "mean"), n=("y", "size"))
    return resumen.reset_index(drop=True)


def evaluar_modelos(df, corte=None):
    corte = corte or config.FECHA_CORTE_EVALUACION
    X, y = features.desde_contactos(df)
    fechas = X["fecha_registro"]
    if not fechas.quantile(0.2) <= pd.Timestamp(corte) <= fechas.quantile(0.8):
        corte = fechas.quantile(0.65).normalize().strftime("%Y-%m-%d")
    X_tr, y_tr, X_te, y_te = dividir_en_el_tiempo(X, y, corte)
    resultados = {
        "corte": str(corte),
        "n_entrenamiento": int(len(y_tr)),
        "n_prueba": int(len(y_te)),
    }
    constante = np.full(len(y_te), y_tr.mean())
    resultados["constante"] = metricas(y_te, constante)
    predicciones = {}
    for tipo in ("logistica", "arbol"):
        modelo = ModeloContacto(tipo).entrenar(X_tr, y_tr)
        predicciones[tipo] = modelo.probabilidad(X_te)
        resultados[tipo] = metricas(y_te, predicciones[tipo])
    bajo, alto = intervalo_auc(y_te, predicciones["logistica"])
    resultados["logistica"]["auc_ic95"] = [bajo, alto]
    resultados["calibracion_logistica"] = calibracion(y_te, predicciones["logistica"]).to_dict("records")
    resultados["ablacion"] = ablacion(X_tr, y_tr, X_te, y_te)
    return resultados, predicciones, (X_te, y_te)


def ablacion(X_tr, y_tr, X_te, y_te):
    conjuntos = {
        "solo_espera": ["rango_espera"],
        "solo_horario": ["franja_hora", "dia_semana"],
        "solo_canal": ["canal"],
        "espera_y_horario": ["rango_espera", "franja_hora", "dia_semana"],
        "horario_y_canal": ["franja_hora", "dia_semana", "canal"],
        "perfil": ["objetivo", "edad", "plan_de_interes"],
        "todo": list(features.COLUMNAS),
    }
    salida = {}
    for nombre, columnas in conjuntos.items():
        modelo = ModeloContacto("logistica", columnas).entrenar(X_tr, y_tr)
        salida[nombre] = float(roc_auc_score(y_te, modelo.probabilidad(X_te)))
    return salida


def tablas_exploratorias(df):
    X, y = features.desde_contactos(df)
    tabla = X.copy()
    tabla["no_contesta"] = 1 - y
    tabla["asesor"] = df.loc[tabla.index, "asesor"]
    salida = {}
    for columna in ("franja_hora", "rango_espera", "canal", "dia_semana", "asesor"):
        salida[columna] = tabla.groupby(columna, observed=True)["no_contesta"].agg(["size", "mean"]).rename(
            columns={"size": "contactos", "mean": "tasa_no_contesta"}
        )
    salida["espera_por_franja"] = pd.crosstab(tabla["franja_hora"], tabla["rango_espera"], normalize="index")
    return salida


def graficar(df, resultados, ruta_exploracion, ruta_calibracion):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tablas = tablas_exploratorias(df)
    orden_franja = ["<9", "9-10", "11-12", "13-15", "16-18", "19+"]
    orden_espera = ["<30min", "30min-2h", "2-6h", "6-12h", "12-24h", ">24h"]
    figura, ejes = plt.subplots(1, 3, figsize=(13, 3.8))
    paneles = [
        ("franja_hora", orden_franja, "Hora del contacto"),
        ("rango_espera", orden_espera, "Espera desde el registro"),
        ("canal", ["Referido", "Google", "Organico", "Meta", "TikTok"], "Canal"),
    ]
    for eje, (columna, orden, titulo) in zip(ejes, paneles):
        datos = tablas[columna].reindex(orden)
        eje.bar(datos.index, datos["tasa_no_contesta"] * 100, color="#2F5597")
        eje.set_title(titulo, fontsize=10)
        eje.set_ylabel("% que no contesta")
        eje.set_ylim(0, 75)
        eje.tick_params(axis="x", labelrotation=30)
        for i, valor in enumerate(datos["tasa_no_contesta"] * 100):
            eje.text(i, valor + 1, f"{valor:.0f}", ha="center", fontsize=8)
    figura.tight_layout()
    figura.savefig(ruta_exploracion, dpi=350)
    plt.close(figura)

    cal = pd.DataFrame(resultados["calibracion_logistica"])
    figura, eje = plt.subplots(figsize=(4.6, 4.2))
    eje.plot([0, 1], [0, 1], linestyle="--", color="gray")
    eje.plot(cal["predicha"], cal["observada"], marker="o", color="#C55A11")
    eje.set_xlabel("Probabilidad predicha de contestar")
    eje.set_ylabel("Proporción observada")
    eje.set_xlim(0.3, 0.9)
    eje.set_ylim(0.3, 0.9)
    eje.set_title("Calibración en el periodo de prueba", fontsize=10)
    figura.tight_layout()
    figura.savefig(ruta_calibracion, dpi=350)
    plt.close(figura)
