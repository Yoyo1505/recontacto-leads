from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data"
SALIDAS = RAIZ / "outputs"
FIGURAS = RAIZ / "docs" / "figuras"
ARCHIVO_LEADS = DATOS / "leads_ficticios.csv"
ARCHIVO_ORIGINAL = ARCHIVO_LEADS
ARCHIVO_ACTUAL = DATOS / "leads_actual.csv"
ARCHIVO_BAJAS = DATOS / "bajas.csv"
HISTORIAL = DATOS / "historial"
VERSIONES_A_CONSERVAR = 20


def ruta_datos_activa():
    return ARCHIVO_ACTUAL if ARCHIVO_ACTUAL.exists() else ARCHIVO_ORIGINAL

MARCA = "Clivi"
MODELO_LLM = "claude-haiku-5-5"

ESPERA_REFERENCIA_H = 18.0
FECHA_CORTE_EVALUACION = "2026-10-25"
HOY_SIMULADO = datetime(2026, 11, 9, 8, 0)

ESTADOS_CANDIDATOS = ("no_contesta", "sin_contactar")
DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


@dataclass(frozen=True)
class Reglas:
    hora_inicio: int = 9
    hora_fin: int = 20
    dias_permitidos: tuple = (0, 1, 2, 3, 4, 5)
    max_intentos: int = 3
    horas_entre_intentos: int = 24
    ventana_dias: int = 21
    capacidad_por_hora: int = 15
    horizonte_dias: int = 3

    def __post_init__(self):
        if not 0 <= self.hora_inicio < self.hora_fin <= 24:
            raise ValueError("El horario debe cumplir 0 <= hora_inicio < hora_fin <= 24")
        if not self.dias_permitidos or any(d not in range(7) for d in self.dias_permitidos):
            raise ValueError("dias_permitidos debe contener numeros de 0 (lunes) a 6 (domingo)")
        for nombre in ("max_intentos", "capacidad_por_hora", "ventana_dias", "horizonte_dias"):
            if getattr(self, nombre) < 1:
                raise ValueError(f"{nombre} debe ser al menos 1")
        if self.horas_entre_intentos < 0:
            raise ValueError("horas_entre_intentos no puede ser negativo")

    @property
    def horas_permitidas(self):
        return tuple(range(self.hora_inicio, self.hora_fin))


REGLAS = Reglas()
