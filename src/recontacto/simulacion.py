"""Simulacion Monte Carlo del recontacto y calculos de potencia para la prueba A/B.

Que responde
    Si recontactamos a la lista del dia con los horarios que propone el modelo, en lugar de en
    horarios sin optimizar, cuantas personas mas contestarian y con que incertidumbre.

Como se construye la incertidumbre
    1. Se vuelve a entrenar el modelo muchas veces sobre remuestras bootstrap de los contactos
       historicos. Cada modelo da probabilidades algo distintas: esa dispersion es la
       incertidumbre del modelo.
    2. En cada corrida se elige un modelo al azar y se sortea quien contesta (Bernoulli).
       Esa dispersion es el azar del muestreo.

El supuesto clave: `alpha`
    En los datos, el horario y la rapidez del contacto estan mezclados, asi que no se sabe que
    parte de la ventaja de un buen horario es causal. `alpha` es la fraccion de esa ventaja que se
    supone real: 0 significa que el horario no importa, 1 que toda la ventaja es causal.
    La probabilidad efectiva con la politica es: p_base + alpha * (p_politica - p_base).

Donde cambiar cosas
    - Numero de modelos bootstrap: `modelos_bootstrap(n=...)`.
    - Politica de referencia ("sin optimizar"): `preparar`, variable `p_base`.
    - Conversion a ventas: `tasa_venta_por_canal`.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from .model import ModeloContacto

SEMILLA = 7


@dataclass
class Preparacion:
    """Probabilidades por lead bajo cada modelo bootstrap (forma: modelos x leads)."""

    p_politica: np.ndarray
    p_base: np.ndarray
    lead_ids: np.ndarray
    canales: np.ndarray

    @property
    def n_leads(self):
        return self.p_politica.shape[1]

    @property
    def n_modelos(self):
        return self.p_politica.shape[0]


def modelos_bootstrap(X, y, n=150, semilla=SEMILLA):
    generador = np.random.default_rng(semilla)
    modelos = []
    while len(modelos) < n:
        indices = generador.integers(0, len(y), len(y))
        muestra_y = y.iloc[indices]
        if muestra_y.nunique() < 2:
            continue
        modelos.append(ModeloContacto("logistica").entrenar(X.iloc[indices], muestra_y))
    return modelos


def preparar(elegibles, marco, asignados, modelos):
    """Calcula, para cada modelo bootstrap, la probabilidad con el horario asignado y la
    probabilidad media sobre todos los horarios posibles (horario sin optimizar)."""
    if marco.empty or len(asignados) == 0:
        vacio = np.zeros((len(modelos), 0))
        return Preparacion(vacio, vacio, np.array([]), np.array([]))
    ids = list(asignados.index)
    clave = marco.merge(
        asignados[["horario"]].reset_index().rename(columns={"horario": "horario_asignado"}),
        on="indice_lead",
    )
    posicion_asignado = np.flatnonzero((clave["horario"] == clave["horario_asignado"]).to_numpy())
    marco_asignado = marco.iloc[posicion_asignado].set_index("indice_lead").loc[ids]
    posicion_lead = marco["indice_lead"].map({lead: i for i, lead in enumerate(ids)})
    en_lista = posicion_lead.notna().to_numpy()
    posiciones = posicion_lead[en_lista].astype(int).to_numpy()
    marco_lista = marco[en_lista]

    p_politica = np.zeros((len(modelos), len(ids)))
    p_base = np.zeros((len(modelos), len(ids)))
    conteo = np.bincount(posiciones, minlength=len(ids))
    for i, modelo in enumerate(modelos):
        p = modelo.probabilidad(marco_lista)
        p_base[i] = np.bincount(posiciones, weights=p, minlength=len(ids)) / conteo
        p_politica[i] = modelo.probabilidad(marco_asignado)
    canales = elegibles.loc[ids, "canal"].to_numpy()
    return Preparacion(p_politica, p_base, np.array(ids), canales)


def tasa_venta_por_canal(df):
    """Proporcion de ventas entre quienes contestaron, por canal (con un minimo de datos)."""
    contactados = df[df["primer_contacto"].notna() & ~df["es_duplicado"]]
    contestaron = contactados[contactados["resultado"] != "no_contesta"]
    por_canal = contestaron.groupby("canal")["resultado"].agg(
        contestaron="size", ventas=lambda s: (s == "venta").sum()
    )
    global_ = por_canal["ventas"].sum() / por_canal["contestaron"].sum()
    por_canal["tasa"] = (por_canal["ventas"] + global_ * 10) / (por_canal["contestaron"] + 10)
    return por_canal["tasa"]


def simular(prep, alpha, n_sim=2000, semilla=SEMILLA, conversion=None):
    """Devuelve un DataFrame con una fila por corrida."""
    generador = np.random.default_rng(semilla)
    if prep.n_leads == 0:
        return pd.DataFrame(
            columns=["contestan_politica", "contestan_base", "diferencia", "tasa_politica", "tasa_base", "ventas_extra"]
        )
    elegidos = generador.integers(0, prep.n_modelos, n_sim)
    p_base = prep.p_base[elegidos]
    p_efectiva = np.clip(p_base + alpha * (prep.p_politica[elegidos] - p_base), 0, 1)
    contestan_politica = generador.random(p_base.shape) < p_efectiva
    contestan_base = generador.random(p_base.shape) < p_base
    pesos = np.zeros(prep.n_leads)
    if conversion is not None:
        pesos = pd.Series(prep.canales).map(conversion).fillna(conversion.mean()).to_numpy()
    diferencia = contestan_politica.sum(axis=1) - contestan_base.sum(axis=1)
    return pd.DataFrame(
        {
            "contestan_politica": contestan_politica.sum(axis=1),
            "contestan_base": contestan_base.sum(axis=1),
            "diferencia": diferencia,
            "tasa_politica": contestan_politica.mean(axis=1),
            "tasa_base": contestan_base.mean(axis=1),
            "ventas_extra": (contestan_politica.astype(float) - contestan_base) @ pesos,
        }
    )


def resumen(corridas):
    if corridas.empty:
        return {"media": 0.0, "ic_bajo": 0.0, "ic_alto": 0.0, "prob_mejora": 0.0, "ventas_extra": 0.0}
    diferencia = corridas["diferencia"]
    return {
        "media": float(diferencia.mean()),
        "ic_bajo": float(np.percentile(diferencia, 2.5)),
        "ic_alto": float(np.percentile(diferencia, 97.5)),
        "prob_mejora": float((diferencia > 0).mean()),
        "ventas_extra": float(corridas["ventas_extra"].mean()),
    }


def sensibilidad_alpha(prep, alphas=None, n_sim=800, conversion=None):
    alphas = np.linspace(0, 1, 11) if alphas is None else alphas
    filas = []
    for alpha in alphas:
        r = resumen(simular(prep, float(alpha), n_sim, conversion=conversion))
        filas.append({"alpha": float(alpha), **r})
    return pd.DataFrame(filas)


def tamano_muestra(p0, delta, potencia=0.8, alfa=0.05):
    """Personas necesarias por brazo para detectar un aumento `delta` sobre la tasa base `p0`
    con una prueba z de dos proporciones, de dos colas."""
    p1 = p0 + delta
    if not 0 < p0 < 1 or not 0 < p1 < 1 or delta == 0:
        raise ValueError("p0 y p0 + delta deben estar entre 0 y 1 y delta no puede ser 0")
    media = (p0 + p1) / 2
    z_alfa = norm.ppf(1 - alfa / 2)
    z_potencia = norm.ppf(potencia)
    numerador = (z_alfa * np.sqrt(2 * media * (1 - media)) + z_potencia * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
    return int(np.ceil(numerador / delta**2))


def potencia_simulada(p0, delta, n, sims=4000, alfa=0.05, semilla=SEMILLA):
    """Fraccion de experimentos simulados en los que la prueba detecta el efecto."""
    generador = np.random.default_rng(semilla)
    a = generador.binomial(n, p0, sims)
    b = generador.binomial(n, np.clip(p0 + delta, 0, 1), sims)
    pa, pb = a / n, b / n
    combinada = (a + b) / (2 * n)
    error = np.sqrt(np.maximum(2 * combinada * (1 - combinada) / n, 1e-12))
    z = (pb - pa) / error
    return float((np.abs(z) > norm.ppf(1 - alfa / 2)).mean())


def curva_potencia(p0, deltas, ns, sims=2000, alfa=0.05):
    filas = []
    for delta in deltas:
        for n in ns:
            filas.append({"delta": delta, "n": int(n), "potencia": potencia_simulada(p0, delta, int(n), sims, alfa)})
    return pd.DataFrame(filas)


def potencia_analitica(p0, delta, n, alfa=0.05):
    """Potencia aproximada de la prueba z de dos proporciones con `n` personas por brazo."""
    p1 = p0 + delta
    media = (p0 + p1) / 2
    z_alfa = norm.ppf(1 - alfa / 2)
    ee_nula = np.sqrt(2 * media * (1 - media))
    ee_alt = np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))
    return float(norm.cdf((abs(delta) * np.sqrt(n) - z_alfa * ee_nula) / ee_alt))
