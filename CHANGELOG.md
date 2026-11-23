# Registro de cambios

Todos los cambios importantes del proyecto se documentan aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/). El detalle técnico de cada versión (decisiones, errores y su corrección) está en [`docs/bitacora.md`](docs/bitacora.md).

Tipos de cambio: **Agregado** · **Cambiado** · **Corregido** · **Eliminado** · **Seguridad**.

## [Sin publicar]

### Agregado
- Resultado de la primera medición real del panel de visibilidad con los motores comerciales (ver `docs/plan_visibilidad_ia.md`).
- Resultados de la prueba con dos personas (ver `docs/prueba_dos_personas.md`).

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
