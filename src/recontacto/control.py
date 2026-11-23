"""Control estadistico: intervalos, carta p y grafico de embudo.

Que responde
    - Cuanto se puede confiar en cada porcentaje (intervalos de Wilson).
    - Si la tasa de "no contesta" es estable en el tiempo o hay dias fuera de lo normal (carta p).
    - Si un asesor se aleja de la tasa global mas de lo que el azar explica (grafico de embudo).

Donde cambiar cosas
    - Anchura de los limites de control: parametro `sigmas` de `carta_p` y `niveles` de `embudo`.
    - Base de calculo: `contactados` (solo primeros contactos de leads sin duplicados).
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

NIVELES_EMBUDO = {"95%": 0.95, "99.8%": 0.998}


def contactados(df):
    c = df[df["primer_contacto"].notna() & ~df["es_duplicado"]].copy()
    c["no_contesta"] = (c["resultado"] == "no_contesta").astype(int)
    return c


def wilson(exitos, n, confianza=0.95):
    """Intervalo de Wilson para una proporcion. Devuelve (bajo, alto)."""
    exitos = np.asarray(exitos, dtype=float)
    n = np.asarray(n, dtype=float)
    z = norm.ppf(1 - (1 - confianza) / 2)
    p = np.divide(exitos, n, out=np.zeros_like(exitos), where=n > 0)
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    ancho = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centro - ancho, centro + ancho


def tabla_con_intervalos(df, columna):
    c = contactados(df)
    t = c.groupby(columna, observed=True)["no_contesta"].agg(n="size", x="sum").reset_index()
    t["tasa"] = t["x"] / t["n"]
    bajo, alto = wilson(t["x"], t["n"])
    t["bajo"], t["alto"] = bajo, alto
    return t


def carta_p(df, sigmas=3.0):
    """Carta p diaria de la proporcion que no contesta, agrupada por fecha de registro."""
    c = contactados(df)
    c["fecha"] = c["fecha_registro"].dt.normalize()
    d = c.groupby("fecha")["no_contesta"].agg(n="size", x="sum").reset_index()
    centro = d["x"].sum() / d["n"].sum()
    error = np.sqrt(centro * (1 - centro) / d["n"])
    d["tasa"] = d["x"] / d["n"]
    d["centro"] = centro
    d["limite_alto"] = np.clip(centro + sigmas * error, 0, 1)
    d["limite_bajo"] = np.clip(centro - sigmas * error, 0, 1)
    d["fuera_de_control"] = (d["tasa"] > d["limite_alto"]) | (d["tasa"] < d["limite_bajo"])
    return d


def embudo(df, columna="asesor", niveles=None):
    """Tasa por grupo contra su tamano, con limites que se cierran al crecer n."""
    niveles = NIVELES_EMBUDO if niveles is None else niveles
    c = contactados(df).dropna(subset=[columna])
    g = c.groupby(columna)["no_contesta"].agg(n="size", x="sum").reset_index()
    g["tasa"] = g["x"] / g["n"]
    centro = c["no_contesta"].mean()
    rango_n = np.linspace(max(5, g["n"].min() * 0.6), g["n"].max() * 1.3, 60)
    limites = pd.DataFrame({"n": rango_n})
    for nombre, nivel in niveles.items():
        z = norm.ppf(1 - (1 - nivel) / 2)
        error = np.sqrt(centro * (1 - centro) / rango_n)
        limites[f"alto_{nombre}"] = np.clip(centro + z * error, 0, 1)
        limites[f"bajo_{nombre}"] = np.clip(centro - z * error, 0, 1)
    z_externo = norm.ppf(1 - (1 - max(niveles.values())) / 2)
    error_g = np.sqrt(centro * (1 - centro) / g["n"])
    g["fuera_de_control"] = (g["tasa"] - centro).abs() > z_externo * error_g
    return g, limites, float(centro)


def tasas_por(X, y, columna):
    """Tasa de "no contesta" por categoria de una variable del modelo, con intervalo de Wilson.

    `X` son las variables del modelo y `y` indica si la persona contesto (1) o no (0).
    """
    tabla = pd.DataFrame({columna: X[columna].to_numpy(), "no_contesta": 1 - y.to_numpy()})
    t = tabla.groupby(columna, observed=True)["no_contesta"].agg(n="size", x="sum").reset_index()
    t["tasa"] = t["x"] / t["n"]
    t["bajo"], t["alto"] = wilson(t["x"], t["n"])
    return t


def por_variante(df):
    """Tasa de respuesta por variante de mensaje, con intervalo de Wilson.

    Supone que `variante` y `resultado` se refieren al mismo intento: lo que contesto la persona
    despues de recibir ese mensaje. Sin columna `variante` o sin datos, devuelve una tabla vacia.
    """
    columnas = ["variante", "n", "contestaron", "tasa", "bajo", "alto"]
    if "variante" not in df.columns:
        return pd.DataFrame(columns=columnas)
    c = contactados(df)
    c = c[c["variante"].fillna("").astype(str).str.strip().ne("")]
    if c.empty:
        return pd.DataFrame(columns=columnas)
    t = c.groupby("variante")["no_contesta"].agg(n="size", no="sum").reset_index()
    t["contestaron"] = t["n"] - t["no"]
    t["tasa"] = t["contestaron"] / t["n"]
    t["bajo"], t["alto"] = wilson(t["contestaron"], t["n"])
    return t[columnas]


def comparar_variantes(df, referencia="A", alfa=0.05):
    """Prueba z de dos proporciones de cada variante contra la de referencia.

    Con varias variantes se hacen varias comparaciones: una diferencia "significativa" suelta debe
    leerse con cuidado (correccion de Bonferroni aplicada al nivel `alfa`).
    """
    t = por_variante(df)
    columnas = ["variante", "n", "tasa", "diferencia", "p_valor", "significativa"]
    if t.empty or referencia not in set(t["variante"]):
        return pd.DataFrame(columns=columnas)
    ref = t[t["variante"] == referencia].iloc[0]
    otras = t[t["variante"] != referencia]
    filas = []
    for _, f in otras.iterrows():
        combinada = (ref["contestaron"] + f["contestaron"]) / (ref["n"] + f["n"])
        error = np.sqrt(combinada * (1 - combinada) * (1 / ref["n"] + 1 / f["n"]))
        z = (f["tasa"] - ref["tasa"]) / error if error > 0 else 0.0
        p = float(2 * (1 - norm.cdf(abs(z))))
        filas.append(
            {"variante": f["variante"], "n": int(f["n"]), "tasa": float(f["tasa"]), "diferencia": float(f["tasa"] - ref["tasa"]), "p_valor": p, "significativa": p < alfa / max(1, len(otras))}
        )
    return pd.DataFrame(filas, columns=columnas)
