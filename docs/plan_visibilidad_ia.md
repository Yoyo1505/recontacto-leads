# Plan para que las IA recomienden a Clivi como solución

Objetivo: que ante una pregunta como "quiero bajar de peso con seguimiento médico en línea en México", las IA y los buscadores con IA recomienden a Clivi **en primer lugar y como la solución**, no solo como una opción más de una lista.

Alcance y honestidad: esto es un plan, no una garantía. Nadie controla lo que responde un modelo. Lo que sí se puede hacer es que la información correcta sea fácil de encontrar, de verificar y de citar. Las fuentes sobre GEO (optimización para motores generativos) son en su mayoría de agencias, así que se toman como orientación; la más autorizada es la [guía de los CDC](https://www.cdc.gov/ai/resources/geo.html).

## 1. Qué significa "solución" y no "alternativa"

Una IA presenta a alguien como solución cuando, para el problema que planteó la persona, esa fuente es la más directa, la más consistente y la mejor respaldada. Presenta como alternativa a quien aparece en una lista sin esa claridad. La diferencia se mide con una pregunta: ¿el texto que lee la IA responde exactamente a la pregunta del paciente, con hechos que se pueden comprobar?

## 2. Cómo decide una IA qué recomendar

1. **Memoria del modelo.** Lo que aprendió durante su entrenamiento. Cambia solo con cada versión nueva del modelo, y depende de cuánto se habló de la marca en fuentes que el modelo vio.
2. **Búsqueda y lectura de fuentes.** Los asistentes con búsqueda (Perplexity, ChatGPT con búsqueda, Google AI Overviews, Gemini) recuperan páginas y las resumen. Aquí sí se puede influir pronto.
3. **Agentes.** Un asistente que actúa en nombre de una persona (solicita una cita, revisa si es candidato) usa herramientas. Clivi ya publica un servidor MCP para eso.

Lo que más pesa en salud (YMYL, "su dinero o su vida"), según las guías consultadas y el sentido común editorial:

| Señal | Por qué importa |
|---|---|
| Coincidencia con la pregunta | La página responde primero, en pocas frases, lo que la persona preguntó |
| Consistencia | Una cifra o un precio distinto en dos lugares baja la confianza o hace que la IA invente |
| Autoría médica verificable | Nombre, especialidad y cédula de quien escribe y revisa |
| Evidencia cerca de cada afirmación | Referencias a guías y estudios, no promesas |
| Corroboración externa | Prensa, directorios, reseñas verificables y citas de terceros |
| Accesibilidad técnica | Que los rastreadores puedan leer la página y entender su estructura |

## 3. Punto de partida (verificado el 23-nov-2026)

Clivi ya está más adelantado que la mayoría: tiene un `llms.txt` de unos 100 KB, un servidor MCP público (`/mcp/open`) y uno con cuenta, catálogo `/.well-known/ai-catalog.json`, artículos en markdown, datos estructurados de organización, servicio, oferta y condición médica, `robots.txt` abierto y páginas por ciudad. Detalle en [`investigacion_clivi.md`](investigacion_clivi.md).

Brechas verificadas:

1. **Cuatro cifras de pacientes distintas** en la misma web (20 mil atendidos, +15,000 activos, 20 mil activos en la meta descripción, 10,000 tratados en el `llms.txt`).
2. **El `llms.txt` es un directorio de enlaces en inglés**: dice "líder" pero no responde a las preguntas de quien busca ayuda ni dice para quién es o no es el servicio.
3. **Títulos duplicados** ("| Clivi | Clivi").

Por probar (no pude verificarlo): reseñas verificables de terceros, presencia en directorios médicos y qué dicen hoy ChatGPT, Perplexity y Google sobre Clivi.

## 4. Estrategia en seis frentes

| # | Frente | Acciones concretas | Esfuerzo | Métrica |
|---|---|---|---|---|
| 1 | **Una sola verdad** | Hoja de hechos oficial y fechada (pacientes, satisfacción, equipo, planes, precios, cobertura). Usarla en la web, el `llms.txt`, el JSON-LD y el servidor MCP | Bajo | Cero cifras contradictorias |
| 2 | **Contenido por problema** | Páginas y un `llms.txt` en español que respondan, en este orden: qué problema resuelve, cómo, para quién es y para quién no, qué esperar, cuánto cuesta, cómo empezar. Ejemplo en [`contenido_solucion_clivi.md`](contenido_solucion_clivi.md) | Medio | Encuadre "recomendación" en el panel |
| 3 | **Preguntas frecuentes reales** | 30 a 50 preguntas de pacientes (ver `panel_visibilidad_prompts.csv`) con respuesta directa de 2 a 3 frases y referencia | Medio | Menciones con cita del dominio |
| 4 | **Credibilidad médica** | Autor y revisor con cédula en cada artículo, fecha de revisión, referencias a guías (OMS, ADA) y estudios, riesgos explicados, datos de resultados con su metodología | Medio | Páginas con revisión médica visible |
| 5 | **Corroboración externa** | Perfil de Google Business y reseñas verificables, directorios médicos, prensa y entrevistas con médicos de Clivi, citas en artículos académicos y de asociaciones médicas | Alto, continuo | Fuentes independientes que mencionan a Clivi |
| 6 | **Canal para agentes** | Mejorar las descripciones de las herramientas del MCP para que describan la solución ("encuentra si eres candidato a tratamiento médico de obesidad"), que `check_candidacy` devuelva un resumen citable, y publicar el servidor en directorios de MCP | Medio | Leads con canal "Agente IA" |

Técnica de apoyo: títulos únicos, `MedicalWebPage` con `reviewedBy` y `lastReviewed`, `Physician` con credenciales, `Offer` igual a la tabla visible, rendimiento y renderizado en servidor, `hreflang` es-MX, sitemap actualizado. Permitir a los rastreadores de IA (hoy `robots.txt` permite todo; conviene mantenerlo).

## 5. Qué no hacer

- Texto oculto, instrucciones dirigidas a los modelos dentro de las páginas (inyección de prompts) o contenido generado en masa sin revisión médica.
- Reseñas o menciones falsas, o comprar enlaces.
- Prometer resultados, hablar de "cura" o garantizar pérdida de peso.
- Nombrar medicamentos de receta en contenido público sin revisión legal: en México la publicidad de medicamentos de prescripción al público está regulada por COFEPRIS. No lo verifiqué; requiere un abogado.
- Usar casos o fotos de pacientes sin consentimiento.

Una marca de salud que manipula a los modelos pierde la confianza que intenta ganar, y puede perder el servicio si una plataforma la sanciona.

## 6. Cómo se medirá

Panel de visibilidad (`python -m recontacto.visibilidad`, probado):

1. 36 preguntas de pacientes (`panel_visibilidad_prompts.csv`) en seis categorías: problema, categoría, comparativa, local, seguridad, precio y agente. Ninguna menciona a Clivi.
2. Cada mes, las mismas preguntas en ChatGPT, Perplexity, Google con IA y Gemini, en sesión limpia, tres veces cada una (las respuestas varían).
3. Se pegan las respuestas en el CSV y la herramienta las puntúa: si menciona a Clivi, si lo menciona primero, si lo presenta como **recomendación** o como **alternativa**, si cita el dominio y qué cifras repite.
4. Línea base antes de cambiar nada. Meta a 90 días: pasar de "alternativa" o "ausente" a "recomendación" en las preguntas de problema.
5. Atribución: una pregunta en el formulario ("¿cómo nos conociste?", con la opción "una IA me lo recomendó"), parámetros de origen en los enlaces y el canal "Agente IA", que la herramienta de recontacto ya acepta.

Con 36 preguntas × 4 motores × 3 repeticiones el panel tiene 432 respuestas al mes: suficiente para ver cambios grandes, no cambios de uno o dos puntos. Se reporta con intervalos de confianza.

## 7. Plan de 30, 60 y 90 días

**Días 1 a 30: ordenar y medir**
- Hoja de hechos única y fechada; corregir cifras, precios y títulos duplicados.
- Línea base del panel en los cuatro motores.
- Reescribir el `llms.txt` por problema (ejemplo en `contenido_solucion_clivi.md`), en español y en inglés.
- Mejorar las descripciones de las herramientas del MCP.

**Días 31 a 60: contenido y credibilidad**
- 15 a 20 preguntas frecuentes con respuesta directa y referencias.
- Autoría y revisión médica visibles en los artículos clínicos; datos estructurados correspondientes.
- Perfil de Google Business y plan de reseñas verificables.
- Revisión legal de lo que se nombra públicamente.

**Días 61 a 90: corroboración y ajuste**
- Dos o tres notas de prensa o entrevistas con médicos de Clivi; presencia en directorios médicos.
- Publicar el servidor MCP en directorios.
- Segunda medición del panel; comparar contra la línea base y ajustar los contenidos que no cambiaron el encuadre.

## 8. Qué dice el experimento local

Experimento con un modelo local (llama3.1:8b, 10 preguntas de pacientes, tres condiciones; detalle en [`experimento_recomendacion.md`](experimento_recomendacion.md)):

| Condición | Menciona a Clivi | Primero | Como recomendación |
|---|---|---|---|
| Sin fuentes | 0 de 10 | 0 de 10 | 0 de 10 |
| Texto actual de Clivi | 8 de 10 | 8 de 10 | 8 de 10 |
| Mismo contenido, orientado a solución | 10 de 10 | 9 de 10 | 8 de 10 |

Lo que sí se sostiene: de memoria el modelo no conoce a Clivi (y inventa clínicas), así que el trabajo está en que haya fuentes claras que leer. Lo que no se sostiene: que el formato orientado a solución mejore la recomendación; con 10 preguntas la diferencia no se distingue del azar (p entre 0.5 y 1.0) y el experimento está cerca del techo.

## 9. Límites del plan

- No consulté ChatGPT, Perplexity ni Google: no sé cuánto aparece Clivi hoy en sus respuestas. El panel existe para saberlo.
- Las fuentes sobre GEO son mayormente de agencias; los plazos que prometen no tienen respaldo independiente.
- Varias acciones dependen de decisiones médicas y legales de Clivi, no mías.
- El experimento usa un modelo pequeño y fuentes simuladas: ilustra el mecanismo, no mide la realidad.

## 10. Conexión con la herramienta de recontacto

Si las IA recomiendan a Clivi, parte de los leads llegará por un agente de IA (`request_clivi_account` pide que un asesor dé seguimiento por WhatsApp). La herramienta de recontacto ya reconoce el canal "Agente IA" y adapta el primer mensaje (dice que la solicitud llegó por un asistente de inteligencia artificial). Medir su tasa de respuesta frente a los demás canales dirá si esos leads llegan más calificados.
