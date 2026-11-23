"""Ensambla web/motor.js y web/app.js a partir de las secciones de web/fuente/.

Por que
    Cada seccion de la herramienta vive en su propio archivo (web/fuente/motor/NN_nombre.js y
    web/fuente/app/NN_nombre.js). Se editan ahi, y este script las une en orden en los dos archivos que
    carga la pagina y que lee `node web/prueba_motor.js`. Los archivos ensamblados se versionan para que
    la pagina funcione sin ningun paso de compilacion.

Uso
    python scripts/ensamblar_web.py            escribe web/motor.js y web/app.js
    python scripts/ensamblar_web.py --revisar  no escribe: falla si los ensamblados no coinciden con las secciones

Donde cambiar cosas
    - Una seccion: su archivo en web/fuente/. El prefijo numerico define el orden.
    - Una seccion nueva: un archivo nuevo con el siguiente numero, empezando con la linea
      `  // ------------------------------------------------------------------ nombre`.
"""

import argparse
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web"
PIEZAS = {"motor": WEB / "motor.js", "app": WEB / "app.js"}


def ensamblar(nombre):
    partes = sorted((WEB / "fuente" / nombre).glob("[0-9][0-9]_*.js"))
    if not partes:
        raise SystemExit(f"No hay secciones en web/fuente/{nombre}")
    return "".join(p.read_text(encoding="utf-8") for p in partes)


def main(argumentos=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--revisar", action="store_true", help="solo comprueba que los ensamblados esten al dia")
    args = parser.parse_args(argumentos)
    desactualizados = []
    for nombre, destino in PIEZAS.items():
        texto = ensamblar(nombre)
        if args.revisar:
            if not destino.exists() or destino.read_text(encoding="utf-8") != texto:
                desactualizados.append(destino.name)
        else:
            destino.write_text(texto, encoding="utf-8", newline="\n")
            print(f"{destino.name}: {len(texto.splitlines())} lineas de {len(list((WEB / 'fuente' / nombre).glob('[0-9][0-9]_*.js')))} secciones")
    if desactualizados:
        print("Desactualizados: " + ", ".join(desactualizados) + ". Corre python scripts/ensamblar_web.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
