"""Datos, modelo y calculos pesados compartidos por todas las secciones.

Se construye una sola vez al arrancar. Los calculos lentos (evaluacion del modelo, modelos
bootstrap, lista del dia para unas reglas dadas) se calculan bajo demanda y se guardan en cache.

Donde cambiar cosas
    - Numero de modelos bootstrap para la simulacion: `N_BOOTSTRAP`.
    - Reglas que llegan desde la barra lateral: `reglas_desde_dict` y `reglas_a_dict`.
    - Fecha por defecto de la lista: `recontacto.config.HOY_SIMULADO`.
"""

from datetime import datetime, time
from functools import cached_property, lru_cache

from recontacto import config, evaluation, features, pipeline
from recontacto import simulacion as sim
from recontacto.config import Reglas
from recontacto.data import cargar_leads, fecha_sugerida, leer_bajas
from recontacto.model import ModeloContacto

N_BOOTSTRAP = 100


def reglas_desde_dict(datos):
    return Reglas(
        hora_inicio=int(datos["hora_inicio"]),
        hora_fin=int(datos["hora_fin"]),
        dias_permitidos=tuple(int(d) for d in datos["dias_permitidos"]),
        max_intentos=int(datos["max_intentos"]),
        horas_entre_intentos=int(datos["horas_entre_intentos"]),
        ventana_dias=int(datos["ventana_dias"]),
        capacidad_por_hora=int(datos["capacidad_por_hora"]),
    )


def reglas_a_dict(reglas):
    return {
        "hora_inicio": reglas.hora_inicio,
        "hora_fin": reglas.hora_fin,
        "dias_permitidos": list(reglas.dias_permitidos),
        "max_intentos": reglas.max_intentos,
        "horas_entre_intentos": reglas.horas_entre_intentos,
        "ventana_dias": reglas.ventana_dias,
        "capacidad_por_hora": reglas.capacidad_por_hora,
    }


class Contexto:
    """Con `ruta_datos` explicita se lee solo ese archivo; sin ella se usa la base activa
    (`data/leads_actual.csv` si existe) y la lista de bajas."""

    def __init__(self, ruta_datos=None):
        self._explicita = ruta_datos
        self.ids_nuevos = []
        self.pendiente = None
        self.version = 0
        self.recargar()

    def recargar(self):
        """Vuelve a leer los datos y descarta todo lo calculado. Se usa tras actualizar la base."""
        if self._explicita is not None:
            self.ruta = self._explicita
            bajas = []
        else:
            self.ruta = config.ruta_datos_activa()
            bajas = leer_bajas(config.ARCHIVO_BAJAS)
        self.version += 1
        self.n_bajas = len(bajas)
        self.df = cargar_leads(self.ruta, bajas)
        self.X, self.y = features.desde_contactos(self.df)
        self.modelo = ModeloContacto("logistica").entrenar(self.X, self.y)
        self.conversion = sim.tasa_venta_por_canal(self.df)
        self._asignacion = lru_cache(maxsize=16)(self._calcular_asignacion)
        self._lista = lru_cache(maxsize=16)(self._calcular_lista)
        self._preparacion = lru_cache(maxsize=8)(self._calcular_preparacion)
        for nombre in ("evaluacion", "modelos_bootstrap"):
            self.__dict__.pop(nombre, None)

    @property
    def fecha_inicial(self):
        return fecha_sugerida(self.df).date()

    @cached_property
    def evaluacion(self):
        return evaluation.evaluar_modelos(self.df)

    @cached_property
    def modelos_bootstrap(self):
        return sim.modelos_bootstrap(self.X, self.y, n=N_BOOTSTRAP)

    @property
    def tasa_contesta(self):
        return float(self.y.mean())

    @property
    def leads_por_dia(self):
        unicos = self.df[~self.df["es_duplicado"]]
        return float(unicos.groupby(unicos["fecha_registro"].dt.normalize()).size().mean())

    def _calcular_asignacion(self, fecha_iso, reglas):
        ahora = datetime.combine(datetime.fromisoformat(fecha_iso).date(), time(8))
        return pipeline.calcular_asignacion(self.df, self.modelo, ahora, reglas)

    def _calcular_lista(self, fecha_iso, reglas):
        ahora = datetime.combine(datetime.fromisoformat(fecha_iso).date(), time(8))
        return pipeline.generar_lista(self.df, self.modelo, ahora, reglas)

    def _calcular_preparacion(self, fecha_iso, reglas):
        elegibles, marco, asignados, _ = self._asignacion(fecha_iso, reglas)
        return sim.preparar(elegibles, marco, asignados, self.modelos_bootstrap)

    def lista(self, estado):
        return self._lista(estado["fecha"], reglas_desde_dict(estado["reglas"]))

    def preparacion(self, estado):
        return self._preparacion(estado["fecha"], reglas_desde_dict(estado["reglas"]))


def estado_inicial(ctx=None, reglas=None):
    fecha = ctx.fecha_inicial if ctx is not None else config.HOY_SIMULADO.date()
    estado = {"fecha": fecha.isoformat(), "reglas": reglas if reglas is not None else reglas_a_dict(config.REGLAS)}
    if ctx is not None:
        estado["version"] = ctx.version
    return estado
