import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import CATEGORICAS, COLUMNAS, NUMERICAS


def _preprocesador(columnas):
    categoricas = [c for c in CATEGORICAS if c in columnas]
    numericas = [c for c in NUMERICAS if c in columnas]
    transformadores = []
    if categoricas:
        transformadores.append(
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categoricas)
        )
    if numericas:
        transformadores.append(
            (
                "num",
                Pipeline([("imp", SimpleImputer(strategy="median")), ("esc", StandardScaler())]),
                numericas,
            )
        )
    return ColumnTransformer(transformadores, sparse_threshold=0)


def _grupo(nombre_transformado, columnas):
    base = nombre_transformado.split("__", 1)[1]
    for columna in sorted(columnas, key=len, reverse=True):
        if base == columna or base.startswith(columna + "_"):
            return columna
    return base


class ModeloContacto:
    def __init__(self, tipo="logistica", columnas=None):
        self.tipo = tipo
        self.columnas = list(columnas) if columnas else list(COLUMNAS)
        if tipo == "logistica":
            clasificador = LogisticRegression(C=1.0, max_iter=1000)
        elif tipo == "arbol":
            clasificador = HistGradientBoostingClassifier(
                max_depth=3, learning_rate=0.05, max_iter=150, random_state=0
            )
        else:
            raise ValueError(f"Tipo de modelo desconocido: {tipo}")
        self.pipeline = Pipeline(
            [("pre", _preprocesador(self.columnas)), ("clf", clasificador)]
        )
        self.media_ = None

    def entrenar(self, X, y):
        self.pipeline.fit(X[self.columnas], y)
        self.media_ = self.pipeline.named_steps["pre"].transform(X[self.columnas]).mean(axis=0)
        return self

    def probabilidad(self, X):
        return self.pipeline.predict_proba(X[self.columnas])[:, 1]

    def contribuciones(self, X):
        if self.tipo != "logistica":
            raise ValueError("Las contribuciones solo existen para el modelo logistico")
        pre = self.pipeline.named_steps["pre"]
        coef = self.pipeline.named_steps["clf"].coef_[0]
        transformado = pre.transform(X[self.columnas])
        aporte = (transformado - self.media_) * coef
        nombres = [_grupo(n, self.columnas) for n in pre.get_feature_names_out()]
        tabla = pd.DataFrame(aporte, columns=nombres, index=X.index)
        return tabla.T.groupby(level=0).sum().T.reindex(columns=self.columnas)
