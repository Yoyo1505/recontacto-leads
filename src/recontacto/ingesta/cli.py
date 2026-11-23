"""Linea de comandos de la ingesta (python -m recontacto.ingesta)."""

import argparse
import sys

import pandas as pd

from .esquema import ErrorIngesta
from .fusion import procesar
from .lectura import leer_fuente
from .simulacion import simular_llegada
from .versiones import agregar_baja, aplicar, listar_versiones, restaurar


def _parser():
    p = argparse.ArgumentParser(description="Actualiza la base de leads desde un archivo, una base de datos o la nube")
    p.add_argument("--origen", help="ruta, URL, cadena de conexion o env:NOMBRE_DE_VARIABLE")
    p.add_argument("--tabla")
    p.add_argument("--consulta", help="SELECT de solo lectura")
    p.add_argument("--hoja", help="hoja de Excel")
    p.add_argument("--aplicar", action="store_true", help="guarda los cambios (sin esto solo se muestra el informe)")
    p.add_argument("--simular", action="store_true", help="muestra que haria la herramienta con las personas nuevas")
    p.add_argument("--listar-versiones", action="store_true")
    p.add_argument("--restaurar", nargs="?", const="ultima", metavar="VERSION")
    p.add_argument("--agregar-baja", metavar="TELEFONO")
    return p


def main(argumentos=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argumentos)
    try:
        if args.listar_versiones:
            versiones = listar_versiones()
            print("\n".join(versiones) if versiones else "No hay versiones guardadas.")
            return 0
        if args.restaurar:
            elegida = restaurar(None if args.restaurar == "ultima" else args.restaurar)
            print(f"Base restaurada a: {elegida}")
            return 0
        if args.agregar_baja:
            print("Telefono agregado a la lista de bajas." if agregar_baja(args.agregar_baja) else "Ese telefono ya estaba en la lista de bajas.")
            return 0
        if not args.origen:
            print("Indica --origen, --listar-versiones, --restaurar o --agregar-baja.")
            return 2
        crudo, descripcion = leer_fuente(args.origen, args.tabla, args.consulta, args.hoja)
        informe = procesar(crudo, descripcion)
        if args.aplicar:
            aplicar(informe)
        print(informe.texto())
        if args.simular:
            pd.set_option("display.width", 220, "display.max_colwidth", 120)
            print("\nQue haria la herramienta con estas personas:")
            print(simular_llegada(informe).to_string(index=False))
        return 0
    except ErrorIngesta as error:
        print(f"Error: {error}")
        return 1
