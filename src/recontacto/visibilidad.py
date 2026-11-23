"""Panel de visibilidad en IA: puntua respuestas de asistentes y buscadores sobre una marca.

Para que sirve
    Medir, mes a mes, si las IA recomiendan a Clivi y como: se hacen las mismas preguntas de pacientes a
    varios motores (ChatGPT, Perplexity, Google, Gemini, un modelo local...), se pegan las respuestas en
    un CSV y esta herramienta las puntua. Los motores comerciales no se consultan desde aqui: las
    respuestas se capturan a mano (o con la API de cada uno) y se leen con el mismo criterio.

Que mide de cada respuesta
    menciona        aparece el nombre de la marca
    primero         aparece en las primeras lineas (primeros 300 caracteres)
    encuadre        ausente, mencion, alternativa o recomendacion (la meta es pasar de "alternativa" a
                    "recomendacion")
    cita            incluye el dominio de la marca (una fuente enlazada)
    cifras          que cifras de pacientes repite (las publicadas hoy no coinciden entre si)
    negativo        la menciona con una advertencia o critica

Donde cambiar cosas
    - Marca y dominio: parametros de `puntuar`.
    - Palabras que definen el encuadre: PATRON_ALTERNATIVA y PATRON_RECOMENDACION.
    - Cifras a vigilar: CIFRAS_CONOCIDAS.

Uso desde la linea de comandos
    python -m recontacto.visibilidad --plantilla docs/panel_visibilidad_prompts.csv --salida respuestas.csv
    python -m recontacto.visibilidad --respuestas respuestas.csv
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .control import wilson

PATRON_ALTERNATIVA = re.compile(r"(alternativa|otra opci[oó]n|otras opciones|tambi[eé]n podr[ií]as|como complemento|puedes considerar tambi[eé]n)")
PATRON_RECOMENDACION = re.compile(r"(recomiend|mejor opci[oó]n|ideal para|es la soluci[oó]n|lo que necesitas|opci[oó]n m[aá]s adecuada|te sugiero)")
PATRON_NEGATIVO = re.compile(r"(no recomiendo|evita|fraude|estafa|quejas|no es confiable|sin respaldo|cuidado con)")
CIFRAS_CONOCIDAS = {"10 mil": r"\b10[ ,.]?000\b|\b10 mil\b", "15 mil": r"\b15[ ,.]?000\b|\b15 mil\b", "20 mil": r"\b20[ ,.]?000\b|\b20 mil\b"}


def puntuar(texto, marca="Clivi", dominio="clivi.com.mx"):
    t = str(texto).lower()
    pos = t.find(marca.lower())
    menciona = pos >= 0
    ventana = t[max(0, pos - 160) : pos + 220] if menciona else ""
    if not menciona:
        encuadre = "ausente"
    elif PATRON_ALTERNATIVA.search(ventana):
        encuadre = "alternativa"
    elif PATRON_RECOMENDACION.search(ventana):
        encuadre = "recomendacion"
    else:
        encuadre = "mencion"
    cifras = [nombre for nombre, patron in CIFRAS_CONOCIDAS.items() if menciona and re.search(patron, t)]
    return {
        "menciona": menciona,
        "primero": menciona and pos < 300,
        "encuadre": encuadre,
        "cita": dominio in t,
        "cifras": ", ".join(cifras),
        "negativo": bool(menciona and PATRON_NEGATIVO.search(ventana)),
    }


def resumir(filas, columna_motor="motor"):
    """Una fila por motor: cuantas respuestas mencionan, recomiendan y citan a la marca, con intervalos."""
    puntos = pd.DataFrame([{columna_motor: f[columna_motor], **puntuar(f["respuesta"])} for f in filas])
    salida = []
    for motor, g in puntos.groupby(columna_motor):
        n = len(g)
        fila = {"motor": motor, "n": n}
        for clave, serie in (
            ("menciona", g["menciona"]),
            ("primero", g["primero"]),
            ("recomendacion", g["encuadre"].eq("recomendacion")),
            ("alternativa", g["encuadre"].eq("alternativa")),
            ("cita", g["cita"]),
        ):
            k = int(serie.sum())
            bajo, alto = wilson([k], [n])
            fila[clave] = k
            fila[clave + "_tasa"] = k / n
            fila[clave + "_ic"] = f"{bajo[0]:.0%} a {alto[0]:.0%}"
        fila["cifras_distintas"] = len({c for cs in g["cifras"] for c in cs.split(", ") if c})
        salida.append(fila)
    return pd.DataFrame(salida)


def plantilla(ruta_prompts, motores=("chatgpt", "perplexity", "google_ai", "gemini")):
    prompts = pd.read_csv(ruta_prompts, dtype=str, encoding="utf-8-sig")
    filas = [{"motor": m, "prompt_id": r["id"], "categoria": r["categoria"], "prompt": r["prompt"], "respuesta": ""} for _, r in prompts.iterrows() for m in motores]
    return pd.DataFrame(filas)


def main(argumentos=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Panel de visibilidad de una marca en respuestas de IA")
    parser.add_argument("--plantilla", help="CSV de preguntas: genera el CSV a llenar con las respuestas")
    parser.add_argument("--salida", default="respuestas.csv")
    parser.add_argument("--respuestas", help="CSV con las columnas motor, prompt_id, respuesta")
    args = parser.parse_args(argumentos)
    if args.plantilla:
        plantilla(args.plantilla).to_csv(args.salida, index=False, encoding="utf-8-sig")
        print(f"Plantilla guardada en {args.salida}. Llena la columna 'respuesta' con lo que contesta cada motor.")
        return 0
    if not args.respuestas:
        print("Indica --plantilla o --respuestas.")
        return 2
    datos = pd.read_csv(args.respuestas, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    datos = datos[datos["respuesta"].str.strip().ne("")]
    if datos.empty:
        print("No hay respuestas llenas en el archivo.")
        return 1
    tabla = resumir(datos.to_dict("records"))
    pd.set_option("display.width", 200)
    print(tabla[["motor", "n", "menciona", "primero", "recomendacion", "alternativa", "cita", "cifras_distintas"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
