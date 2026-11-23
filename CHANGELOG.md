# Registro de cambios

Todos los cambios importantes del proyecto se documentan aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/). El detalle técnico de cada versión (decisiones, errores y su corrección) está en [`docs/bitacora.md`](docs/bitacora.md).

Tipos de cambio: **Agregado** · **Cambiado** · **Corregido** · **Eliminado** · **Seguridad**.

## [Sin publicar]

### Agregado
- Resultado de la primera medición real del panel de visibilidad con los motores comerciales (ver `docs/plan_visibilidad_ia.md`).
- Resultados de la prueba con dos personas (ver `docs/prueba_dos_personas.md`).

## [0.9.0] · 2026-11-23

Cambios a partir de la prueba con dos personas: les costó identificar las pestañas de la herramienta e interpretar los datos.

### Cambiado
- **Pestañas guiadas.** Las 8 pestañas se numeran del 1 al 8 y se agrupan en "Para trabajar cada día" (Lista del día, Mensajes, Respuestas, Datos) y "Para entender si funciona" (Evidencia, Simulación, Prueba A/B, Límites). Cada una dice su pregunta ("¿A quién contacto hoy?", "¿Qué le escribo?"...). Un recuadro indica "Pestaña N de 8", explica qué hay ahí y trae los botones Anterior y Siguiente. Antes eran ocho botones sueltos con solo su nombre, en otro orden.
- El video se regrabó para mostrar la nueva barra de pestañas y las lecturas.

### Agregado
- **Interpretación de los datos en palabras sencillas.** La pestaña Evidencia abre con un resumen de seis frases calculadas con los datos y dos gráficas nuevas: "El canal importa" y "La rapidez importa". Cada gráfica de Evidencia, Simulación y Prueba A/B trae un "Cómo leerlo" con las cifras reales (los textos se recalculan con los datos y los parámetros). La Prueba A/B dice en una frase cuánta gente y cuántos días hacen falta.
- **Lista del día:** gráfica "Quiénes están en la lista, por canal" y un glosario de columnas ("¿Qué significa cada columna?").
- `verificar_web.py` comprueba las pestañas con su pregunta, la guía "Pestaña N de 8", el botón Siguiente, el resumen de Evidencia y las lecturas de cada gráfica.
- La prueba con dos personas queda registrada en la entrega 4, el memo, la bitácora de la página y `docs/prueba_dos_personas.md`, solo con lo observado.

### Corregido
- Dos cifras distintas del porcentaje que no contesta convivían en la herramienta: 40.3% (de 1,694 contactados) y 39.2% (de 1,624, sin los 70 registros con teléfono repetido). El resumen de Evidencia ahora explica ambas.

## [0.8.1] · 2026-11-23

### Eliminado
- La portada "Inicio" con las cuatro entregas: el menú de cada página ya enlaza las cuatro. `index.html` queda solo como una redirección a `herramienta.html` para que la dirección raíz del sitio siga funcionando. El logo enlaza a la herramienta.

### Cambiado
- El sitio tiene cuatro páginas (herramienta, memo, bitácora y video) y el menú, cuatro enlaces.
- El video se regrabó: la última escena muestra la entrega 4 en lugar de la portada.

## [0.8.0] · 2026-11-23

La entrega pasa de una sola página a cuatro entregas separadas, cada una con su propio enlace, y se corrige el formato en pantallas angostas.

### Cambiado
- **Una página por entrega** en `web/sitio/`: `index.html` (portada), `herramienta.html` (1), `memo.html` (2), `bitacora.html` (3) y `video.html` (4). Antes todo estaba en una sola página con vistas por ancla. Solo la herramienta carga el motor y los datos (las demás páginas pesan unos 35 KB).
- `web/plantilla.html` se reemplaza por `web/paginas/` (`base.html` y el contenido de cada entrega). `construir_web.py` arma las cinco páginas.
- El video se regrabó (3:01): la última escena muestra la portada con las cuatro entregas.
- `bat\abrir_version_web.bat` abre la portada.

### Agregado
- Entrega 4 con una tabla de **demos para simular** (7 recorridos con qué hacer y qué debe pasar, con las cifras verificadas) junto al video y la prueba con dos personas.
- `scripts/revisar_responsivo.py`: abre cada página a 8 anchos (de 1440 a 360 px, incluida la media pantalla) y falla si algo se sale de la ventana; guarda capturas.
- `verificar_web.py` recorre también las otras cuatro páginas (menú, contenido, video, 7 demos, prueba pendiente).

### Corregido
- **Se perdía el formato en pantalla dividida.** Por debajo de 1,100 px la herramienta pasaba a una columna, pero la columna `1fr` no podía encogerse por debajo del ancho de sus tablas y pestañas, así que la página se desbordaba hasta 833 px en una ventana de 683. Se cambió a `minmax(0, 1fr)`, se agregaron cortes a 1,100, 960, 720 y 420 px y los `minmax` de las rejillas ya no superan el ancho disponible. Revisado de 360 a 1,440 px: cero desbordes en las cinco páginas.
- El texto de la herramienta decía "reglas de la izquierda" aun cuando en pantallas angostas quedan arriba.

## [0.7.0] · 2026-11-23

Versión de preparación para producción: código seccionado, documentación operativa y análisis de pendientes. No cambia el comportamiento de la lista del día.

### Agregado
- `docs/ANALISIS_PENDIENTES.md`: qué falta para producción, por prioridad (P0 a P3), con esfuerzo y criterio de terminado.
- `docs/ARQUITECTURA.md`, `docs/OPERACION.md`, `docs/SEGURIDAD_Y_PRIVACIDAD.md` y `docs/CONTRIBUIR.md`.
- README en cada carpeta (`src/recontacto`, `app`, `web`, `scripts`, `bat`, `tests`, `data`).
- Secciones **Mensajes** y **Respuestas** en la aplicación Dash (antes solo en la versión web).
- `scripts/ensamblar_web.py`: une las secciones de `web/fuente/` en `web/motor.js` y `web/app.js`; `--revisar` falla si están desactualizados.
- Flujo de integración continua (`.github/workflows/ci.yml`): pruebas de Python, comparación de JavaScript contra Python y comprobación de los archivos ensamblados.
- `recontacto.__version__`.
- Resultado del experimento de recomendación con un modelo local (`docs/experimento_recomendacion.md`).

### Cambiado
- `src/recontacto/ingesta.py` (650 líneas) pasa a ser el paquete `src/recontacto/ingesta/` con siete módulos (`esquema`, `utilidades`, `lectura`, `validacion`, `fusion`, `versiones`, `simulacion`) y `cli`. Las importaciones existentes (`from recontacto import ingesta`) y `python -m recontacto.ingesta` siguen funcionando.
- `web/motor.js` (798 líneas) y `web/app.js` (784 líneas) pasan a editarse como 12 y 14 archivos en `web/fuente/`; los archivos ensamblados son byte a byte iguales a los anteriores.
- El video se regrabó (3:01) con las pestañas Mensajes y Respuestas en lugar de las conversaciones ilustradas.
- El memo y la bitácora de la página reflejan mensajes por situación, lectura de respuestas, el modelo local y el plan de visibilidad.

### Corregido
- La investigación de Clivi listaba dos cifras de pacientes contradictorias; son cuatro en la misma web (20 mil atendidos, +15,000 activos, 20 mil activos y 10,000 tratados).
- El informe del experimento mostraba intervalos negativos ("-0%") y un límite con el número de preguntas equivocado.

### Corregido (CI)
- `fsspec` faltaba en `requirements.txt`: la primera corrida de CI falló en 2 pruebas de lectura desde la nube.

### Pruebas
- 229 pruebas (antes 221): secciones nuevas de Dash y verificación de que los archivos web estén ensamblados.

## [0.6.0] · 2026-11-23

### Agregado
- Mensajes por situación: tres pasos (primer contacto, retomar, cierre) con variantes A, B y C asignadas de forma estable por persona (`crc32`), que cambian según el canal (asistente de IA) y los días desde la solicitud.
- Validador de fidelidad (menciona la solicitud, sigue la estrategia de la variante, no mezcla "tú" y "usted") además del de seguridad.
- Medición de variantes: `control.por_variante` y `control.comparar_variantes`; columna opcional `variante` en la ingesta.
- Lectura de respuestas (`respuestas.py`): baja, no le interesa, quiere seguir, cita, pide otro momento, pregunta, malestar o emergencia y ambigua, con motivo visible; seguridad antes que baja y baja antes que todo.
- Cliente de Ollama (`ClienteOllama`) y prueba del modelo local (`scripts/probar_llm_local.py`).
- Pestañas **Mensajes** y **Respuestas** en la versión web; el motor JavaScript replica variantes y clasificador.
- Plan de visibilidad en IA (`docs/plan_visibilidad_ia.md`), ejemplo de contenido orientado a solución, panel de 36 preguntas y `recontacto.visibilidad`.

### Corregido
- El clasificador perdía la hora en "mañana a las 4", tomaba "no puedo hoy" como cita y "¿me pueden llamar a las 6?" como pregunta.
- Mensajes de un modelo local pasaban seguridad pero no la situación (0 de 12); con el prompt de reescritura y el validador de fidelidad, 5 de 12 pasan ambos.

## [0.5.0] · 2026-11-23

### Agregado
- Versión web (`web/`) que abre sin instalar nada: motor en JavaScript, memo, bitácora, video y prueba con dos personas en una página, publicada en GitHub Pages.
- Comparación automática de JavaScript contra Python (`node web/prueba_motor.js`) y verificación en Chrome real (`scripts/verificar_web.py`).
- Video de tres minutos (`scripts/crear_video.py`) con capítulos.

### Corregido
- Plotly no publica la versión 2.35.2 en cdnjs; se carga desde jsDelivr.

## [0.4.0] · 2026-11-23

### Agregado
- Ingesta de datos desde CSV, JSON, Excel, Parquet, SQLite, bases SQL, URLs y nube, con informe previo, validación fila por fila, fusión por `lead_id` y versiones restaurables.
- Lista de bajas (`data/bajas.csv`) con prioridad sobre cualquier otra regla.
- Sección **Datos** en la aplicación y archivos `.bat` para cada tarea (`bat/menu.bat`).

### Corregido
- pandas no admite cadenas vacías en columnas enteras con nulos: los números se guardan como texto.
- Un aviso de error aparecía sin que nadie hiciera clic: se protegieron los callbacks contra el disparo inicial.

## [0.3.0] · 2026-11-23

### Agregado
- Aplicación en Dash con Plotly dividida en secciones (reemplaza a Streamlit) con la identidad visual de Clivi.
- Simulación Monte Carlo con incertidumbre del modelo y parámetro `alpha`, tamaño de muestra y potencia de la prueba A/B.
- Control estadístico: intervalos de Wilson, carta p y gráfico de embudo por asesor.

### Eliminado
- `app/streamlit_app.py`.

## [0.2.0] · 2026-11-23

### Cambiado
- Las reglas de trato pasan a un objeto `Reglas` validado, ajustable desde la aplicación y la línea de comandos.

## [0.1.0] · 2026-11-23

### Agregado
- Primera versión: limpieza de datos, reglas de trato, modelo de probabilidad de contestar por horario (regresión logística), asignación con límite por hora, plantillas de mensaje con validador y aplicación inicial.

[Sin publicar]: https://github.com/Yoyo1505/recontacto-leads/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/Yoyo1505/recontacto-leads/releases/tag/v0.7.0
