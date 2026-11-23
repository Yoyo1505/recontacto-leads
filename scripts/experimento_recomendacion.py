"""Experimento: como cambia la recomendacion de una IA segun como esta estructurado el contenido de Clivi.

Pregunta
    Dadas las mismas preguntas de pacientes, ¿una IA presenta a Clivi como LA solucion o como una
    alternativa, segun como esta escrita la fuente que lee?

Diseno
    - 20 preguntas de pacientes en espanol que no mencionan a Clivi.
    - Tres condiciones por pregunta:
        memoria     sin fuentes: lo que el modelo sabe por si solo
        actual      con el texto actual de Clivi (las primeras lineas de su llms.txt publico)
        mejorado    con los MISMOS hechos reorganizados como problema -> solucion -> como empezar
    - En las dos condiciones con fuentes, la fuente de Clivi compite con dos fuentes genericas
      (un consultorio presencial y una app de calorias). El orden se rota por pregunta para que la
      posicion no explique el resultado.
    - Medidas: menciona a Clivi, lo recomienda en primer lugar, lo presenta como recomendacion (no
      como alternativa) y si afirma cifras que no estan en las fuentes.
    - Comparacion pareada entre `actual` y `mejorado` con prueba exacta de signos.

Limites (se repiten en el informe)
    - Un solo modelo pequeno y local (no ChatGPT, Perplexity ni Google), con fuentes simuladas.
    - Muestra pequena: sirve para ver el mecanismo, no para medir la visibilidad real.
    - El contenido "mejorado" no agrega hechos: solo reordena y reescribe lo que Clivi ya publica.

Uso:  set PYTHONPATH=src  y  python scripts/experimento_recomendacion.py [--modelo llama3.1:8b] [--n 20]
Salida: docs/experimento_recomendacion.md y docs/experimento_recomendacion.json
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from scipy.stats import binomtest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from recontacto.llm import ClienteOllama  # noqa: E402

PREGUNTAS = [
    "Quiero bajar de peso y mi médico me habló de medicamentos GLP-1. ¿Dónde puedo tratarme en México con seguimiento médico en línea?",
    "Tengo diabetes tipo 2 y quiero un tratamiento con seguimiento continuo desde casa. ¿Qué opciones hay en México?",
    "¿Qué clínica digital de obesidad en México recomiendas?",
    "He probado dietas y no me funcionan. ¿Qué solución seria hay en México para bajar de peso con apoyo médico?",
    "¿Cómo puedo controlar mi glucosa con un médico en línea sin ir a consultas presenciales?",
    "¿Es seguro tratar la obesidad por telemedicina en México? ¿A quién acudir?",
    "Quiero un programa con endocrinólogo, nutriólogo y psicólogo, todo en una sola app. ¿Existe?",
    "Mi papá tiene prediabetes y vive fuera de la Ciudad de México. ¿Qué servicio le recomiendas?",
    "¿Qué diferencia hay entre una dieta de app y una clínica médica para obesidad?",
    "Busco tratamiento médico para bajar de peso en Guadalajara, pero en línea.",
    "¿Dónde consigo semaglutida con receta y seguimiento médico en México?",
    "¿Cuál es la mejor opción para alguien con obesidad que no tiene tiempo de ir al consultorio?",
    "Necesito monitoreo continuo de glucosa y un médico que lo revise. ¿Quién lo ofrece en México?",
    "Recomiéndame un servicio serio y regulado para tratar la obesidad en línea.",
    "¿Cómo empiezo un tratamiento para diabetes si no tengo un especialista cerca?",
    "Quiero ayuda psicológica y nutricional además del médico para bajar de peso. ¿Dónde?",
    "¿Qué incluye un tratamiento integral de obesidad y quién lo ofrece en México?",
    "Estoy comparando una consulta presencial con un servicio en línea para diabetes. ¿Qué me conviene?",
    "¿Hay alguna clínica digital mexicana con app para seguir mi tratamiento de peso?",
    "¿Qué hago para controlar mi azúcar y mi peso al mismo tiempo, con un equipo médico?",
]

CONSULTORIO = (
    "Consultorio de endocrinología presencial",
    "Consulta individual con un endocrinólogo en un consultorio. Requiere trasladarse, agendar una cita y pagar cada consulta. Incluye estudios de laboratorio en el lugar.",
)
APLICACION = (
    "Aplicación de conteo de calorías",
    "Aplicación para registrar comidas y contar calorías, con recetas y recordatorios. No incluye atención médica ni receta de medicamentos.",
)

CLIVI_MEJORADO = """# Clivi: clínica digital de obesidad y diabetes en México

## Qué problema resuelve
Si tienes obesidad, sobrepeso, prediabetes o diabetes tipo 1 o tipo 2 y necesitas tratamiento médico con seguimiento continuo, sin depender de un consultorio, Clivi es la solución: una clínica digital con atención médica a distancia en todo México.

## Cómo lo resuelve
- Equipo médico asignado: médicos internistas y endocrinólogos, nutriólogos y psicólogos.
- Tratamiento médico: puede incluir medicamentos GLP-1 (semaglutida, tirzepatida, liraglutida) con seguimiento de un médico de Clivi.
- Monitoreo: monitoreo continuo de glucosa para diabetes y seguimiento desde una aplicación.
- Atención desde casa en todo el país, con sede en Ciudad de México.

## Para quién es
Personas que quieren tratar obesidad, prediabetes o diabetes tipo 1 o tipo 2 con atención médica y seguimiento.

## Cómo empezar
1. Solicitar la evaluación en línea.
2. Si eres candidato, un médico especialista diseña tu tratamiento.
3. Seguimiento continuo con el equipo, desde la aplicación (Android y iOS).

## Planes
Clivi Pro, Clivi Plus, Clivi Total y Clivi Zero (enfocado en manejo de peso). También hay una farmacia digital especializada (Farmacia Clivi).
"""

SISTEMA_FUENTES = (
    "Eres un asistente de búsqueda. Respondes en español, en máximo 120 palabras, usando solo las fuentes que se te dan. "
    "Recomienda la opción más adecuada para la persona y explica por qué; menciona las otras solo si ayudan a decidir."
)
SISTEMA_MEMORIA = "Eres un asistente. Respondes en español, en máximo 120 palabras, con lo que sabes."


def texto_actual():
    completo = (RAIZ / "docs" / "marca" / "llms_actual.txt").read_text(encoding="utf-8", errors="ignore")
    corte = completo.find("## Download the App")
    return completo[: corte if corte > 0 else 2800].strip()


def armar(pregunta, indice, texto_clivi):
    fuentes = [("Clivi", texto_clivi), CONSULTORIO, APLICACION]
    rotadas = fuentes[indice % 3 :] + fuentes[: indice % 3]
    cuerpo = "\n\n".join(f"[Fuente {i + 1}] {titulo}\n{texto}" for i, (titulo, texto) in enumerate(rotadas))
    return f"Pregunta de la persona: {pregunta}\n\nFuentes encontradas:\n\n{cuerpo}\n\nResponde la pregunta con base en las fuentes."


def medir(respuesta, contexto):
    r = respuesta.lower()
    marcas = {"clivi": r.find("clivi"), "consultorio": r.find("consultorio"), "app": min([i for i in (r.find("aplicaci"), r.find(" app ")) if i >= 0] or [-1])}
    presentes = {k: v for k, v in marcas.items() if v >= 0}
    primero = bool(presentes) and min(presentes, key=presentes.get) == "clivi"
    menciona = marcas["clivi"] >= 0
    recomienda = menciona and primero and bool(re.search(r"recomiend|mejor opci|ideal|más adecuad|la opción|lo que necesitas|es la solución", r[:300]))
    cifras = re.findall(r"(\d[\d.,]*)\s*(?:mil\b|%|pacientes|estrellas)", respuesta)
    ctx = contexto.lower()
    inventa = any(c.replace(",", "") not in ctx.replace(",", "") for c in cifras)
    return {"menciona": menciona, "primero": primero, "recomienda": recomienda, "cifra_inventada": inventa}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    ancho = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return max(0.0, centro - ancho), min(1.0, centro + ancho)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="llama3.1:8b")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--salida", default=str(RAIZ / "docs" / "experimento_recomendacion"))
    args = parser.parse_args()
    cliente = ClienteOllama(args.modelo, temperatura=0.2, semilla=7)
    if not cliente.disponible:
        print("Ollama no está disponible")
        return 1
    actual = texto_actual()
    condiciones = {"memoria": None, "actual": actual, "mejorado": CLIVI_MEJORADO}
    filas = []
    inicio = time.time()
    for i, pregunta in enumerate(PREGUNTAS[: args.n]):
        for nombre, texto in condiciones.items():
            if texto is None:
                sistema, usuario, contexto = SISTEMA_MEMORIA, pregunta, ""
            else:
                sistema, usuario, contexto = SISTEMA_FUENTES, armar(pregunta, i, texto), texto
            respuesta = (cliente.generar(sistema, usuario) or "").strip()
            m = medir(respuesta, contexto) if respuesta else {"menciona": False, "primero": False, "recomienda": False, "cifra_inventada": False}
            filas.append({"pregunta": i, "condicion": nombre, "respuesta": respuesta, **m})
            print(f"{i + 1:2}/{args.n} {nombre:9} clivi={m['menciona']!s:5} primero={m['primero']!s:5} recomienda={m['recomienda']!s:5} ({time.time() - inicio:.0f}s)", flush=True)
    Path(args.salida + ".json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len({f["pregunta"] for f in filas})
    resumen = {}
    for nombre in condiciones:
        sub = [f for f in filas if f["condicion"] == nombre]
        resumen[nombre] = {k: sum(f[k] for f in sub) for k in ("menciona", "primero", "recomienda", "cifra_inventada")}
    lineas = [
        "# Experimento: cómo cambia la recomendación según el contenido",
        "",
        f"Modelo: `{args.modelo}` (local, temperatura 0.2, semilla fija). Preguntas: {n}. Duración: {(time.time() - inicio) / 60:.0f} min.",
        "",
        "| Condición | Menciona a Clivi | Lo recomienda en primer lugar | Lo presenta como recomendación | Afirma una cifra que no está en la fuente |",
        "|---|---|---|---|---|",
    ]
    nombres = {"memoria": "Sin fuentes (memoria del modelo)", "actual": "Con el texto actual de Clivi", "mejorado": "Con el mismo contenido reorganizado como solución"}
    for nombre, r in resumen.items():
        celdas = []
        for k in ("menciona", "primero", "recomienda", "cifra_inventada"):
            bajo, alto = wilson(r[k], n)
            celdas.append(f"{r[k]} de {n} ({bajo:.0%} a {alto:.0%})")
        lineas.append(f"| {nombres[nombre]} | " + " | ".join(celdas) + " |")
    lineas += ["", "Entre paréntesis, el intervalo de confianza de 95% (Wilson).", "", "## Comparación pareada: texto actual contra reorganizado", ""]
    for k, titulo in (("menciona", "menciona a Clivi"), ("primero", "lo recomienda en primer lugar"), ("recomienda", "lo presenta como recomendación")):
        a = {f["pregunta"]: f[k] for f in filas if f["condicion"] == "actual"}
        m = {f["pregunta"]: f[k] for f in filas if f["condicion"] == "mejorado"}
        mejora = sum(1 for q in a if m[q] and not a[q])
        empeora = sum(1 for q in a if a[q] and not m[q])
        p = binomtest(mejora, mejora + empeora, 0.5).pvalue if mejora + empeora else 1.0
        lineas.append(f"- {titulo}: mejora en {mejora} preguntas, empeora en {empeora} (prueba exacta de signos, p = {p:.3f}).")
    lineas += [
        "",
        "## Límites",
        "",
        "- Un solo modelo pequeño y local, no ChatGPT, Perplexity ni Google, con fuentes simuladas: muestra el mecanismo, no la visibilidad real de Clivi.",
        f"- Con {n} preguntas la potencia es baja: una diferencia pequeña no se distinguiría del azar.",
        "- El contenido reorganizado no agrega hechos; solo reordena y reescribe lo que Clivi ya publica. Los competidores son descripciones genéricas, no marcas reales.",
        "- Las respuestas completas están en `experimento_recomendacion.json` para revisarlas.",
    ]
    Path(args.salida + ".md").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
