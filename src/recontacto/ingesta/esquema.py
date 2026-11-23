"""Esquema de la ingesta: columnas, sinonimos, valores validos, errores y el informe.

Donde cambiar cosas
    - Columnas obligatorias y sinonimos: `REQUERIDAS` y `SINONIMOS`.
    - Valores validos de `resultado`: `RESULTADOS` y `SINONIMOS_RESULTADO`.
    - Formatos de fecha aceptados: `FORMATOS_FECHA`.
"""

import re
from dataclasses import dataclass, field

import pandas as pd

COLUMNAS = [
    "lead_id",
    "fecha_registro",
    "canal",
    "anuncio",
    "estado",
    "edad",
    "objetivo",
    "plan_de_interes",
    "telefono",
    "asesor",
    "primer_contacto",
    "resultado",
    "monto_venta",
]
REQUERIDAS = ("lead_id", "fecha_registro", "canal", "telefono", "resultado")
OPCIONALES = ("baja", "variante")
RESULTADOS = ("no_contesta", "sin_contactar", "en_seguimiento", "no_interesado", "venta")
SINONIMOS = {
    "lead_id": {"id", "id_lead", "lead", "folio", "leadid"},
    "fecha_registro": {"fecha", "fecha_de_registro", "fecha_alta", "created_at", "registro"},
    "canal": {"fuente", "origen", "source", "channel"},
    "anuncio": {"ad", "creativo"},
    "estado": {"entidad", "estado_republica", "entidad_federativa", "state"},
    "edad": {"age"},
    "objetivo": {"motivo_de_consulta", "goal"},
    "plan_de_interes": {"plan", "plan_interes"},
    "telefono": {"celular", "whatsapp", "tel", "phone", "telefono_celular"},
    "asesor": {"agente", "advisor", "asignado"},
    "primer_contacto": {"fecha_primer_contacto", "contacted_at", "primer_contacto_fecha"},
    "resultado": {"status", "resultado_final", "etapa"},
    "monto_venta": {"monto", "importe", "monto_de_venta"},
    "baja": {"no_contactar", "opt_out", "unsubscribe"},
    "variante": {"variante_mensaje", "mensaje_variante"},
}
SINONIMOS_RESULTADO = {"contesto": "en_seguimiento", "no_contestó": "no_contesta", "nuevo": "sin_contactar"}
CANALES_CONOCIDOS = {"meta": "Meta", "tiktok": "TikTok", "google": "Google", "referido": "Referido", "organico": "Organico"}
FORMATOS_FECHA = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
)
SEGUIMIENTO = ("resultado", "primer_contacto", "asesor", "monto_venta", "plan_de_interes", "edad", "objetivo", "anuncio", "entidad", "canal", "variante")
ESQUEMAS_BASE_DE_DATOS = {"sqlite", "postgresql", "postgres", "mysql", "mariadb", "mssql", "oracle"}
SQL_PROHIBIDO = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|attach|pragma|exec|replace)\b", re.I)
LIMITE_BYTES = 200 * 1024 * 1024


class ErrorIngesta(Exception):
    """Problema que impide leer o procesar la fuente; el mensaje dice como resolverlo."""


@dataclass
class Informe:
    origen: str = ""
    filas_leidas: int = 0
    columnas_mapeadas: dict = field(default_factory=dict)
    columnas_ignoradas: list = field(default_factory=list)
    validos: int = 0
    rechazados: pd.DataFrame = field(default_factory=pd.DataFrame)
    advertencias: list = field(default_factory=list)
    agregados: list = field(default_factory=list)
    actualizados: dict = field(default_factory=dict)
    sin_cambio: int = 0
    conflictos: list = field(default_factory=list)
    fusionado: pd.DataFrame = None
    version_guardada: str = None
    aplicado: bool = False

    @property
    def hay_cambios(self):
        return bool(self.agregados or self.actualizados)

    def texto(self):
        lineas = [
            f"Origen: {self.origen}",
            f"Filas leidas: {self.filas_leidas}",
            f"Validas: {self.validos} | Rechazadas: {len(self.rechazados)} | Advertencias: {len(self.advertencias)}",
            f"Nuevas: {len(self.agregados)} | Actualizadas: {len(self.actualizados)} | Sin cambio: {self.sin_cambio} | Conflictos: {len(self.conflictos)}",
        ]
        if self.columnas_ignoradas:
            lineas.append("Columnas ignoradas: " + ", ".join(map(str, self.columnas_ignoradas)))
        if len(self.rechazados):
            lineas.append("Motivos de rechazo:")
            conteo = self.rechazados["motivo"].str.replace(r":.*$", "", regex=True).value_counts()
            lineas.extend(f"  {n} x {m}" for m, n in conteo.items())
        for lead, mensaje in self.advertencias[:10]:
            lineas.append(f"  Aviso {lead}: {mensaje}")
        if len(self.advertencias) > 10:
            lineas.append(f"  ... y {len(self.advertencias) - 10} avisos mas")
        if self.aplicado:
            lineas.append(f"Cambios guardados. Copia de la version anterior: {self.version_guardada or 'no hacia falta (base original intacta)'}")
        else:
            lineas.append("No se guardo nada (usa --aplicar para guardar).")
        return "\n".join(lineas)
