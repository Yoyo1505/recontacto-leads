# Investigación sobre Clivi y visibilidad en IA y buscadores

Fecha de consulta: 23-nov-2026. Todo lo marcado como verificado se leyó directamente de las páginas públicas de Clivi ese día. Lo demás es interpretación y se indica como tal.

## 1. Qué es Clivi

- Clínica digital de obesidad y diabetes en México, con médico internista o endocrinólogo, nutriólogo y psicólogo asignados, monitoreo continuo de glucosa y tratamiento con medicamentos GLP-1 (verificado en el sitio y en su `llms.txt`).
- Ciudad de México como sede y atención a todo el país por telemedicina. Páginas locales para CDMX y Guadalajara.
- Planes Clivi Pro, Plus, Total y Zero. Precios vistos en la web: desde $1,599 al mes en la página de planes, $4,299 el primer mes en la portada y $5,499 en la página de obesidad.
- Farmacia propia (farmaciaclivi.com.mx) y aplicación móvil en Android e iOS.
- La prensa la describe como una clínica con modelo distinto al de la consulta tradicional y la ubica también en Chile, Colombia y Perú: [Expansión](https://expansion.mx/tecnologia/2026/02/12/salud-tecnologia-diabetes-reducen-costo), [El Financiero](https://www.elfinanciero.com.mx/opinion/de-jefes/2025/09/17/clivi-simplifica-la-salud/), [Mexico Business News](https://mexicobusiness.news/health/news/digitalization-creates-accessible-chronic-disease-management), [Cathay Innovation](https://cathayinnovation.com/company/clivi/).

## 2. Identidad visual usada en la herramienta

Valores extraídos del HTML y las hojas de estilo públicas del sitio.

| Uso | Color |
|---|---|
| Azul principal (botones, títulos) | `#00547C` |
| Azul secundario | `#006A9C` |
| Azul oscuro (fondos, texto fuerte) | `#002D42` |
| Casi negro azulado | `#0B1F2C` |
| Azul muy claro (fondos de sección) | `#E6F1F7` |
| Gris claro | `#F4F5F5` |
| Verde turquesa (página legal) | `#00A99D` |
| Verde WhatsApp (botón de contacto) | `#25D366` y `#128C7E` |

Tipografía: Inter. Logo: `https://www.clivi.com.mx/logo-clivi.webp` (copia en `docs/marca/`). El logo es marca de Clivi y se usa aquí solo para este demo.

## 3. Lo que Clivi ya hace para ser encontrado por IA y buscadores (verificado)

- `llms.txt` de unos 100 KB con descripción de la empresa, páginas principales, blog por temas y sección legal.
- Servidor MCP propio para asistentes de IA, con una versión sin inicio de sesión (`/mcp/open`) y otra con cuenta (OAuth 2.1). Herramientas como `request_clivi_account` y `check_candidacy`. Catálogo en `/.well-known/ai-catalog.json` y ficha en `/.well-known/mcp.json`.
- Versiones en markdown de los artículos del blog.
- Datos estructurados JSON-LD: `MedicalOrganization`, `LocalBusiness`, `MedicalBusiness`, `Service`, `Offer`, `MedicalCondition`, `MedicalWebPage`, `Person`, `BreadcrumbList`, `WebSite` con `SearchAction` y enlaces `sameAs` a Facebook, LinkedIn e Instagram.
- `robots.txt` abierto, dos mapas del sitio (sitio y blog), URL canónica y páginas por ciudad.

## 4. Brechas y hallazgos

Verificados:

1. Cifras distintas sobre el tamaño, en cuatro lugares de la misma web: la tarjeta de la portada dice "más de 20 mil pacientes atendidos", la franja de confianza de la portada dice "+15,000 pacientes activos", la meta descripción dice "más de 20 mil pacientes activos" y el `llms.txt` dice "más de 10,000 pacientes tratados". Algunas pueden ser métricas distintas (atendidos contra activos), pero no se explica, y El Financiero habla de más de 10 mil. Para un modelo de lenguaje, cifras contradictorias reducen la confianza al citar y dan pie a que invente una.
2. Título duplicado: la portada y la página de obesidad terminan en "| Clivi | Clivi".

No verificados, por probar:

3. No encontré reseñas de pacientes de terceros en mis búsquedas; aparecen notas de prensa y perfiles de médicos individuales en Doctoralia, que no corresponden a Clivi. La búsqueda que usé está limitada, así que esto debe confirmarse revisando Google Maps, tiendas de aplicaciones y directorios.
4. No pude consultar ChatGPT, Perplexity ni Google AI Overviews, así que no sé cuánto aparece hoy Clivi en esas respuestas. Hay que medirlo (sección 6).
5. Velocidad de carga y Core Web Vitals: no medidos.

## 5. Qué recomendar

El contexto es salud, donde las IA y Google exigen más evidencia. Las fuentes que consulté son en su mayoría blogs de agencias, así que lo tomo como orientación y no como medición; la más autorizada es la [guía de GEO de los CDC](https://www.cdc.gov/ai/resources/geo.html).

| Prioridad | Acción | Por qué |
|---|---|---|
| 1 | Una sola fuente de verdad para cifras, precios y nombres de planes, usada en la web, el `llms.txt`, el JSON-LD y el servidor MCP | Datos coherentes son más citables |
| 2 | Autoría médica visible en cada artículo: nombre, especialidad, cédula, fecha de revisión, y reflejarla en `Person` y `MedicalWebPage` | La autoría con credenciales es la señal de confianza más mencionada para salud ([Valtech](https://valtech.com/blog/generative-engine-optimization-healthcare), [DexCare](https://dexcare.com/resources/articles/geo-for-healthcare-websites-a-practical-guide/)) |
| 3 | Citar guías y estudios junto a cada afirmación clínica | Se reporta que los motores favorecen evidencia cerca de la afirmación |
| 4 | Reputación de terceros: perfil de Google Business, reseñas verificables, directorios médicos y prensa | Las IA contrastan con fuentes externas |
| 5 | Páginas locales con contenido real por ciudad (no copias con el nombre cambiado) | Evita páginas de relleno |
| 6 | Corregir títulos duplicados y revisar velocidad | Corrección técnica barata |
| 7 | Publicar el servidor MCP en directorios públicos de servidores y verificar que `check_candidacy` responda con datos correctos | Es una ventaja que casi nadie en el sector tiene |
| 8 | Revisión legal de la mención de medicamentos de receta por nombre comercial en contenido público | Posible riesgo regulatorio con COFEPRIS; no lo verifiqué, requiere revisión de un abogado |

## 6. Cómo medir si funciona

Panel de visibilidad en IA: 20 preguntas reales de pacientes (por ejemplo "clínica para bajar de peso con GLP-1 en México") por 4 motores (ChatGPT, Perplexity, Google AI Overviews, Gemini). Registrar si menciona a Clivi, si la cita con enlace, si las cifras son correctas y el tono. Repetir cada mes. Para atribución, usar un parámetro de origen en los enlaces y un canal "Agente de IA" en el formulario.

## 7. Conexión con la herramienta de recontacto

El servidor MCP de Clivi permite que un asistente de IA pida abrir una cuenta y que "un asesor dé seguimiento por WhatsApp". Eso significa que las IA pueden convertirse en un canal de entrada de leads. Es una hipótesis, no un dato: si los leads que llegan por agentes llegan ya pre-calificados, deberían contestar más, y habría que medirlo como un canal nuevo en este mismo análisis. La herramienta de recontacto ya admite un canal adicional sin cambios de código.

## 8. Límites de esta investigación

- Mi búsqueda web está limitada a resultados de Estados Unidos, y no consulté chatbots ni Google.
- Las guías de GEO que encontré son mayormente de agencias; los plazos que prometen (por ejemplo primeras citaciones en 60 a 120 días) no tienen respaldo independiente.
