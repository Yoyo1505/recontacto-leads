# Experimento: cómo cambia la recomendación según el contenido

Modelo: `llama3.1:8b` (local, temperatura 0.2, semilla fija). Preguntas: 10. Duración: 49 min.

| Condición | Menciona a Clivi | Lo recomienda en primer lugar | Lo presenta como recomendación | Afirma una cifra que no está en la fuente |
|---|---|---|---|---|
| Sin fuentes (memoria del modelo) | 0 de 10 (0% a 28%) | 0 de 10 (0% a 28%) | 0 de 10 (0% a 28%) | 0 de 10 (0% a 28%) |
| Con el texto actual de Clivi | 8 de 10 (49% a 94%) | 8 de 10 (49% a 94%) | 8 de 10 (49% a 94%) | 0 de 10 (0% a 28%) |
| Con el mismo contenido reorganizado como solución | 10 de 10 (72% a 100%) | 9 de 10 (60% a 98%) | 8 de 10 (49% a 94%) | 0 de 10 (0% a 28%) |

Entre paréntesis, el intervalo de confianza de 95% (Wilson).

## Comparación pareada: texto actual contra reorganizado

- menciona a Clivi: mejora en 2 preguntas, empeora en 0 (prueba exacta de signos, p = 0.500).
- lo recomienda en primer lugar: mejora en 1 pregunta, empeora en 0 (prueba exacta de signos, p = 1.000).
- lo presenta como recomendación: mejora en 1 pregunta, empeora en 1 (prueba exacta de signos, p = 1.000).

## Límites

- Un solo modelo pequeño y local, no ChatGPT, Perplexity ni Google, con fuentes simuladas: muestra el mecanismo, no la visibilidad real de Clivi.
- Con 10 preguntas la potencia es baja: una diferencia pequeña no se distinguiría del azar.
- El contenido reorganizado no agrega hechos; solo reordena y reescribe lo que Clivi ya publica. Los competidores son descripciones genéricas, no marcas reales.
- Las respuestas completas están en `experimento_recomendacion.json` para revisarlas.

## Lectura de los resultados

- **Sin fuentes, el modelo no conoce a Clivi**: 0 de 10 menciones, y en la respuesta que revisé inventó clínicas con nombres que no corresponden a nada que se le haya dado. Esto es lo que pasa cuando una IA responde de memoria: la visibilidad depende de que haya fuentes que lea.
- **Con fuentes, Clivi ya aparece casi siempre** (8 de 10 con el texto actual), porque aquí compite contra dos descripciones genéricas. El experimento está cerca del techo y no distingue bien entre dos textos buenos.
- **El texto reorganizado como solución dio algo más** (10 de 10 menciones, 9 de 10 en primer lugar), pero con 10 preguntas la diferencia no es estadísticamente distinguible (p = 0.5 a 1.0). No se puede afirmar que el formato mejore la recomendación; el experimento solo muestra que no la empeora y que no inventa cifras (0 de 10 en las tres condiciones).
- Para medir el efecto real hacen falta competidores con marcas reales, más preguntas y los motores comerciales, que es lo que hace el panel de `docs/plan_visibilidad_ia.md`.
