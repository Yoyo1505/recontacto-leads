"""Prueba la generacion de mensajes con un modelo de lenguaje local (Ollama) y mide cuantos pasan el validador.

Que mide
    Para cada situacion (etapa, variante, canal, antiguedad) pide un mensaje al modelo y lo valida con
    las mismas reglas que las plantillas. Si no pasa, se usa la plantilla de respaldo. Reporta el
    porcentaje que pasa a la primera y cuales reglas se rompen.

Requisitos: Ollama corriendo con el modelo (por defecto llama3.1:8b).
Uso:  set PYTHONPATH=src  y  python scripts/probar_llm_local.py [--modelo llama3.1:8b] [--n 12]
Salida: docs/prueba_llm_local.md
"""

import argparse
import itertools
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from recontacto import mensajes  # noqa: E402
from recontacto.llm import ClienteOllama  # noqa: E402


def situaciones(n):
    base = []
    for etapa, canal, dias in itertools.product(("primer_contacto", "retoma", "cierre"), ("Meta", "Agente IA"), (1, 5)):
        for letra in sorted(mensajes.BIBLIOTECA[etapa]):
            base.append(
                {
                    "etapa": etapa,
                    "contexto": {
                        "intento": {"primer_contacto": 1, "retoma": 2, "cierre": 3}[etapa],
                        "nunca_contactado": etapa == "primer_contacto",
                        "ultimo_intento": etapa == "cierre",
                        "franja_dia": "hoy por la tarde",
                        "asesor": "Asesor B",
                        "variante": letra,
                        "origen_ia": canal == "Agente IA",
                        "dias": dias,
                    },
                }
            )
    return [base[i * len(base) // n] for i in range(min(n, len(base)))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="llama3.1:8b")
    parser.add_argument("--n", type=int, default=12)
    parser.add_argument("--salida", default=str(RAIZ / "docs" / "prueba_llm_local.md"))
    args = parser.parse_args()
    cliente = ClienteOllama(args.modelo)
    if not cliente.disponible:
        print(f"Ollama no está disponible con el modelo {args.modelo}")
        return 1
    filas, problemas = [], {}
    inicio = time.time()
    for caso in situaciones(args.n):
        t = time.time()
        crudo = cliente.generar(mensajes.SISTEMA, mensajes.construir_prompt(caso["contexto"]))
        texto = (crudo or "").strip().strip('"').strip()
        seguro = mensajes.validar_mensaje(texto) if texto else mensajes.ResultadoValidacion(False, ["sin respuesta"])
        resultado = mensajes.validar_mensaje(texto, caso["contexto"]) if texto else seguro
        for p in resultado.problemas:
            problemas[p] = problemas.get(p, 0) + 1
        filas.append({"etapa": caso["etapa"], "variante": caso["contexto"]["variante"], "seguro": seguro.valido, "valido": resultado.valido, "problemas": resultado.problemas, "texto": texto, "segundos": time.time() - t})
        print(f"{'ok ' if resultado.valido else 'NO '} {caso['etapa']:15} {caso['contexto']['variante']} {resultado.problemas}")
    validos = sum(f["valido"] for f in filas)
    seguros = sum(f["seguro"] for f in filas)
    lineas = [
        "# Prueba de generación de mensajes con un modelo local",
        "",
        f"Modelo: `{args.modelo}` (Ollama, en esta computadora). Casos: {len(filas)}. Duración: {time.time() - inicio:.0f} s.",
        "",
        f"- Pasan las reglas de seguridad (sin salud, sin promesas, con baja): **{seguros} de {len(filas)}** ({seguros / len(filas):.0%}).",
        f"- Pasan además la fidelidad (mencionan la solicitud, siguen la estrategia de la variante y no mezclan usted con tú): **{validos} de {len(filas)}** ({validos / len(filas):.0%}).",
        "- Lo que no pasa se reemplaza por la plantilla.",
        "",
        "Reglas que se rompen:",
    ]
    lineas += [f"- {k}: {v} veces" for k, v in sorted(problemas.items(), key=lambda x: -x[1])] or ["- ninguna"]
    lineas += ["", "## Ejemplos", ""]
    for f in filas[:6]:
        lineas.append(f"**{f['etapa']} / variante {f['variante']}** ({'válido' if f['valido'] else 'rechazado: ' + ', '.join(f['problemas'])})")
        lineas.append("")
        lineas.append("> " + " ".join(f["texto"].split()))
        lineas.append("")
    lineas.append("Conclusión: pasar las reglas de seguridad no basta, porque un mensaje seguro puede ser peor que la plantilla. Por eso hay una segunda revisión de fidelidad, y la plantilla es el valor por defecto.")
    Path(args.salida).write_text(chr(10).join(lineas), encoding="utf-8")
    print(f"seguros {seguros}/{len(filas)}, seguros y fieles {validos}/{len(filas)} -> {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
