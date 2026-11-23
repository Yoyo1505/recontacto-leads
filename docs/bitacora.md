# Bitácora técnica

Registro de cambios del proyecto de recontacto de leads. Cada entrada indica qué cambió, por qué y con qué resultado. Las entradas nuevas van arriba.

## 0.8.1 (23-nov-2026)

- Se eliminó la portada "Inicio": con el menú de cuatro entregas en cada página era redundante. `index.html` ahora solo redirige a la herramienta (si no, la dirección raíz del sitio publicado dejaría de abrir algo). Se quitaron la página, sus estilos y sus comprobaciones, y se regrabó el video porque su última escena mostraba la portada.

## 0.8.0 (23-nov-2026)

### Una entrega por página
- La entrega tiene cuatro partes y ahora cada una es su propia página con su propio enlace: herramienta, memo, bitácora y video con demos y prueba con dos personas. Hay además una portada. Las páginas viven en `web/paginas/` (`base.html` común y un archivo por entrega) y `construir_web.py` las arma en `web/sitio/`.
- La entrega 4 incluye ahora siete demos para simular, con qué hacer y qué debe pasar (346 personas; 342 con máximo de 2 intentos; 8 plantillas válidas; cita a las 16:00; la pregunta de precio y el malestar pasan a un asesor; un "NO" saca a la persona de la lista; dos personas nuevas llevan la base de 1,811 a 1,813).
- Un error durante el cambio: al quitar las vistas por ancla, la herramienta no dibujaba la lista porque la primera pintura la hacía la función de rutas. Lo detectó el verificador en Chrome y se movió a la función de arranque.

### Formato en pantalla dividida
- Síntoma: con la ventana a media pantalla, la página se salía del ancho. Se escribió `scripts/revisar_responsivo.py` para medirlo en lugar de adivinarlo: abre cada página a ocho anchos y lista los elementos que se salen.
- Causa: en una sola columna, `grid-template-columns: 1fr` equivale a `minmax(auto, 1fr)` y no se encoge por debajo del contenido; las tablas y pestañas empujaban la columna hasta 833 px en una ventana de 683. Solución: `minmax(0, 1fr)` y `min-width: 0` en los hijos, cortes a 1,100, 960, 720 y 420 px y `minmax(min(Npx, 100%), 1fr)` en las rejillas.
- Resultado: cero desbordes de 360 a 1,440 px en las cinco páginas. No se probó en un teléfono real ni con lectores de pantalla.

## 0.7.0 (23-nov-2026)

### Seccionado del código
- `ingesta.py` (650 líneas) pasó a ser el paquete `ingesta/` con módulos por responsabilidad: `esquema`, `utilidades`, `lectura`, `validacion`, `fusion`, `versiones`, `simulacion` y `cli`. `__init__.py` reexporta los mismos nombres, así que ni la aplicación ni las pruebas cambiaron de importación, y `python -m recontacto.ingesta` sigue funcionando.
- Un error durante la división: la aplicación fallaba con un 500 porque `decisiones_para` no estaba reexportada. Lo detectó la prueba del flujo completo de datos en la aplicación.
- `web/motor.js` y `web/app.js` se editan ahora como 12 y 14 archivos en `web/fuente/`. `scripts/ensamblar_web.py` los une en orden; se comprobó que el resultado es idéntico byte a byte al archivo anterior. `construir_web.py` ensambla primero, y una prueba falla si los ensamblados no coinciden con las secciones.
- La aplicación Dash tiene ahora las secciones Mensajes y Respuestas (antes solo existían en la web), con prueba de cada una y de sus callbacks.

### Documentación para producción
- `docs/ANALISIS_PENDIENTES.md` (qué falta, por prioridad P0 a P3, con esfuerzo, criterio de terminado y riesgos), `ARQUITECTURA.md`, `OPERACION.md`, `SEGURIDAD_Y_PRIVACIDAD.md` y `CONTRIBUIR.md`; README en cada carpeta; `CHANGELOG.md` en la raíz; versión 0.7.0 en `pyproject.toml` y `recontacto.__version__`.
- `.github/workflows/ci.yml` con pruebas de Python, comparación contra JavaScript y comprobación de los ensamblados. No se ha ejecutado en GitHub.

### Experimento de recomendación
- Con llama3.1:8b y 10 preguntas: sin fuentes no menciona a Clivi (0 de 10) e inventa clínicas; con el texto actual lo menciona 8 de 10; con el mismo contenido reorganizado como solución, 10 de 10 (9 en primer lugar). La diferencia entre los dos textos no es estadísticamente distinguible (p entre 0.5 y 1.0). El experimento tardó 49 minutos en CPU.

## 0.6.0 (23-nov-2026)

### Qué mensaje se envía, según la situación (`mensajes.py`)
- Antes había una sola redacción por paso. Ahora hay tres pasos (primer contacto, retomar, cierre) con variantes A, B y C que usan estrategias distintas (por ejemplo: recordar la solicitud, ofrecer elegir horario, dar espacio). A cada persona le toca siempre la misma variante (`crc32` del lead y la etapa), así se puede comparar después.
- El texto cambia si la solicitud llegó por un asistente de IA y si pasaron tres días o más.
- Se agregó un segundo validador, de fidelidad: el mensaje debe mencionar la solicitud, seguir la estrategia de su variante y no mezclar "tú" con "usted". El de seguridad no cambió.
- Medición: `control.por_variante` y `control.comparar_variantes` (dos proporciones contra la variante A). Se puede subir una columna `variante` con los datos. Hoy no hay datos de variantes: es una hipótesis por probar.

### Leer las respuestas (`respuestas.py`)
- Clasificador por reglas, sin modelo: baja, no le interesa, quiere seguir, propone día u hora, pide otro momento, pregunta, malestar o emergencia, ambigua. Cada decisión trae su motivo.
- Prioridad: seguridad antes que baja, baja antes que todo lo demás. Una pregunta o una respuesta ambigua pasa a un asesor; no se responde sola. Un malestar remite a un médico o al 911, no a ventas.
- Errores corregidos durante las pruebas: perdía la hora en "mañana a las 4", trataba "no puedo hoy" como una cita y "¿me pueden llamar a las 6?" como una pregunta.
- Se puede probar por línea de comandos (`python -m recontacto.respuestas --texto "..."`) y en la página, pestaña Respuestas.

### Modelo de lenguaje local (`llm.py`, `scripts/probar_llm_local.py`)
- Cliente para Ollama además del de Anthropic. Primera prueba con llama3.1:8b: 12 de 12 mensajes seguros, 0 de 12 fieles a la situación. El prompt pedía "escribir" en lugar de "reescribir" una base.
- Con el prompt de reescritura y un muestreo equilibrado de situaciones: 6 de 12 seguros y 5 de 12 seguros y fieles (`docs/prueba_llm_local.md`). Conclusión: un modelo pequeño local no es confiable aquí; por eso el texto sale de plantillas y el modelo solo reescribe si pasa los dos validadores.

### Página web (`web/`)
- Pestañas nuevas "Mensajes" (biblioteca por situación, personas por variante, validez, interruptor para comparar variantes) y "Respuestas" (conversación de ejemplo con respuesta, qué entiende, qué hace, y aplicarlo a los datos).
- El motor JavaScript incluye variantes y el clasificador. `node web/prueba_motor.js`: coincide con Python (346 leads, 16 plantillas, 35 respuestas, diferencia máxima de probabilidad 1.1e-16).
- `scripts/verificar_web.py` en Chrome real: 38 comprobaciones, incluidas las dos pestañas nuevas y que un "NO" saque a la persona de la lista.

### Visibilidad en IA
- `docs/plan_visibilidad_ia.md`: plan a 90 días para que las IA presenten a Clivi como solución, no como alternativa. Incluye lo que no debe hacerse y los límites.
- `docs/contenido_solucion_clivi.md`: ejemplo de `llms.txt` y páginas orientadas al problema del paciente.
- `src/recontacto/visibilidad.py` y `docs/panel_visibilidad_prompts.csv`: panel de 36 preguntas que puntúa respuestas de cualquier motor (menciona, primero, recomendación o alternativa, cita, cifras).
- `scripts/experimento_recomendacion.py`: experimento con un modelo local (texto actual contra reorganizado). Resultados en `docs/experimento_recomendacion.md`.
- Hallazgo corregido en la investigación: son cuatro cifras de pacientes distintas en la misma web, no dos.

### Pruebas
- 229 pruebas pasan (antes 168).

## 0.5.0 (23-nov-2026)

### Versión web que abre sin instalar nada (`web/`)
- La entrega pide una herramienta que abra sin instalar. La lógica se reescribió en JavaScript (`web/motor.js`) y se publica como una sola página (`web/entrega.html`) que contiene la herramienta, el memo, la bitácora, el video y la prueba con dos personas.
- `scripts/exportar_web.py` calcula con Python lo que la web necesita (datos, coeficientes del modelo y de 100 modelos bootstrap, series de evidencia y una lista de referencia) y `scripts/construir_web.py` arma la página a partir de `web/plantilla.html`, `estilos.css`, `motor.js` y `app.js`.
- El motor replica la limpieza, las reglas de trato, las probabilidades por horario, la asignación con límite por hora, las explicaciones, los mensajes y su validador, la simulación Monte Carlo, los cálculos de la prueba A/B y la ingesta (leer, validar y fusionar CSV, JSON y Excel).
- Verificación: `node web/prueba_motor.js` compara contra Python lead por lead. Resultado: las mismas 346 recomendaciones, en el mismo orden, con los mismos horarios, motivos y mensajes, y una diferencia máxima de probabilidad de 1e-16. También coinciden las exclusiones por motivo, el tamaño de muestra de la prueba A/B (4,094 y 559) y, dentro de la tolerancia del muestreo, la simulación.
- `scripts/verificar_web.py` prueba la página en un Chrome real: librerías, lista (346), cambio de regla (342), subir el ejemplo de dos personas (1,813), registrar una baja, volver a la base original (1,811), las cuatro vistas y cero errores de JavaScript.
- Límites de esta versión: el modelo no se reentrena en el navegador, no lee Parquet, bases de datos ni la nube, y las bajas viven en el navegador (`localStorage`). Todo eso lo hace la versión en Python.
- Un error corregido: Plotly no publica la versión 2.35.2 en cdnjs; se carga desde jsDelivr (`plotly.js-dist-min`).

### Video de tres minutos (`scripts/crear_video.py`)
- El video pasó de 84 s a 2:58: se agregaron una tarjeta del problema, escenas de la página web, y tarjetas de lo encontrado, lo que no funciona y lo que sigue. La tasa de bits se bajó a 1.5 Mbps (11.1 MB) para caber en el límite del enlace publicado.
- `docs/demo/capitulos.json` guarda en qué segundo empieza cada capítulo y la página lo lee para mostrarlos.
- Las conversaciones de ejemplo siguen marcadas como ilustrativas.

### Pruebas
- 168 pruebas. Nuevas: el motor web contra Python (si Node está instalado) y que la página armada no tenga marcadores pendientes.

## 0.4.0 (23-nov-2026)

### Ingesta de datos (`ingesta.py`)
- Lectura desde CSV, JSON, JSON por líneas, Excel, Parquet, SQLite, bases SQL por SQLAlchemy y direcciones web, S3, Google Cloud y Azure (estas últimas con `fsspec` y la librería de cada servicio, que se instala aparte). `leer_bytes` sirve también para los archivos que se suben desde la aplicación.
- Las cadenas de conexión pueden venir de una variable de entorno (`env:NOMBRE`) y se enmascaran en cualquier mensaje. Las consultas SQL son solo de lectura: un único `SELECT`, sin `;` ni instrucciones que modifiquen datos, y el nombre de tabla se valida.
- Normalización de columnas con sinónimos, aviso de las columnas ignoradas y error claro si faltan las obligatorias.
- Validación fila por fila con motivo de rechazo (lead_id vacío o repetido, fecha, canal, teléfono o resultado no válidos) y avisos que no rechazan (edad fuera de rango, venta sin monto, contacto anterior al registro). Lo rechazado se guarda en `outputs/rechazados_*.csv`.
- Fusión por `lead_id`: agrega, actualiza solo lo que cambió y nunca borra. Un mismo `lead_id` con otro teléfono se rechaza como conflicto.
- Versionado: `data/leads_actual.csv` con una copia de cada versión anterior en `data/historial/` (se conservan 20) y restauración por nombre o a la base original. La base original nunca se modifica. La escritura es atómica.
- Un error corregido durante las pruebas: pandas no admite cadenas vacías en columnas enteras con valores nulos, por lo que los números se convierten a texto al guardar.
- `simular_llegada` muestra qué haría la herramienta con las personas nuevas sin guardar nada; `decisiones_para` es la parte reutilizada por la aplicación.

### Cuidado de las personas
- Lista de bajas (`data/bajas.csv`) y columna opcional `baja`: quien pidió no recibir mensajes queda excluido con el motivo "baja", que tiene prioridad sobre cualquier otro, y sobrevive a restaurar versiones.
- Una misma persona se identifica por los últimos 10 dígitos del teléfono, de modo que distintos formatos del mismo número cuentan como repetidos.

### Aplicación
- Sección nueva **Datos**: subir un archivo, agregar una persona con formulario, registrar una baja y restaurar versiones. Todo pasa por la misma validación y pide confirmación antes de guardar.
- `Contexto.recargar()` vuelve a leer los datos y limpia las cachés tras cualquier cambio; la fecha de la lista pasa a ser el día siguiente al último registro.
- Los callbacks de la sección usan salidas duplicadas permitidas y se protegen contra el disparo inicial de Dash al insertar componentes. Un error corregido: sin esa protección aparecía un aviso de error sin que nadie hubiera hecho clic.
- La fecha de corte de la evaluación del modelo se ajusta sola si los datos nuevos dejan fuera la fecha fija.

### Archivos .bat (`bat/`)
- `menu.bat` y un archivo por tarea: instalar, instalar soporte de nube y bases, iniciar la aplicación, lista del día, simular dos personas, actualizar desde archivo, base o nube, registrar baja, restaurar, evaluar, probar y grabar el demo. Comparten `_entorno.bat` (carpeta, rutas y Python) y `_actualizar.bat` (informe, confirmación y guardado en dos pasos).
- Verificados ejecutándolos, incluido un ciclo completo en una copia aislada: actualizar desde Parquet, registrar una baja, generar la lista (la persona con baja no aparece), volver a subir el mismo archivo (sin cambios) y restaurar la base original.

### Pruebas
- 166 pruebas (53 nuevas): todos los formatos, SQLite y cadenas de conexión, descarga por HTTP con un servidor local, consultas peligrosas, secretos enmascarados, validaciones, fusión, versiones, bajas, qué pasaría con dos personas nuevas, línea de comandos y el flujo completo en la aplicación (subir, aplicar, baja y restaurar).
- Sin probar: conexiones reales a S3, Google Cloud, Azure, PostgreSQL y MySQL (sin credenciales ni conectores instalados).

## 0.3.0 (23-nov-2026)

### Aplicación en Dash
- La interfaz pasa de Streamlit a Dash con Plotly, dividida en secciones independientes (`app/secciones/`): resumen, lista del día, evidencia, simulación, prueba A/B y límites. Cada una expone la misma interfaz (`ID`, `TITULO`, `RUTA`, `layout`, `registrar`) y documenta en su encabezado qué muestra y dónde cambiarla. Se elimina `app/streamlit_app.py`.
- Piezas comunes en `tema.py` (colores y plantilla de Plotly), `componentes.py` (tarjeta, KPI, gráfica) y `contexto.py` (datos, modelo y cálculos pesados en caché).
- Identidad visual tomada del sitio público de Clivi: colores, tipografía Inter y logo.
- Las gráficas son funciones `figura_*` puras. Un error corregido durante la revisión visual: Plotly interpretaba categorías como "9-10" como fechas, por lo que los ejes ahora se fijan como categóricos.
- El estado compartido (fecha y reglas) vive en un `dcc.Store`; reglas no válidas muestran un aviso y no cambian la lista.
- Se separa `calcular_asignacion` de `generar_lista` en `pipeline.py` para reutilizarlo en la simulación.

### Simulación (`simulacion.py`)
- Monte Carlo con 100 modelos bootstrap (incertidumbre del modelo) y Bernoulli por persona (azar del muestreo). Compara el horario asignado contra un horario sin optimizar.
- Parámetro `alpha`: fracción de la ventaja del horario que se supone causal, porque horario y rapidez del contacto están confundidos en los datos. La probabilidad efectiva es `p_base + alpha * (p_politica - p_base)`.
- Resultado: con alpha 0.5, +5.7 personas de 346 (IC 95%: −20 a +31); con alpha 1, +11 (IC: −16 a +38). La mejora de un día no se distingue del azar.
- Ventas extra esperadas con la conversión histórica por canal, suavizada hacia el promedio global: menos de una por lista.
- Potencia y tamaño de muestra para la prueba A/B (prueba z de dos proporciones): +3 puntos requiere unas 4,100 personas por grupo. La fórmula analítica se contrasta con simulación y el error tipo I simulado queda cerca de 5%.

### Control estadístico (`control.py`)
- Intervalos de Wilson para las proporciones.
- Carta p diaria con límites de 3 sigmas: 1 de 42 días fuera de control.
- Gráfico de embudo por asesor (95% y 99.8%): ninguno fuera de los límites. Las diferencias entre asesores caben en el azar.

### Pruebas
- 113 pruebas. Nuevas: simulación y control, figuras de cada sección, enrutamiento y una prueba que dispara cada callback de la app contra el servidor y falla si se agrega uno sin valores de prueba.

### Herramientas
- `scripts/grabar_demo.py` maneja un Chrome temporal por CDP, recorre la aplicación con interacciones reales y arma `docs/demo/demo.gif`.

## 0.2.0 (23-nov-2026)

### Reglas ajustables
- Las reglas de trato pasan de constantes sueltas en `config.py` a un objeto inmutable `Reglas` (horario, días permitidos, máximo de intentos, horas entre intentos, ventana de recuperación, capacidad por hora y horizonte). `policy.py` y `pipeline.py` lo reciben como parámetro, con `REGLAS` como valor por defecto.
- `Reglas` valida sus valores al crearse (horario coherente, al menos un día, máximos positivos). Un valor inválido lanza `ValueError` en lugar de producir una lista incorrecta.
- La interfaz tiene controles para el horario, los días, el máximo de intentos, las horas entre intentos, la ventana y la capacidad por hora. Si las reglas no son válidas, muestra el error y no calcula la lista. La pestaña de reglas refleja los valores activos.
- La línea de comandos acepta `--max-intentos`, `--hora-inicio`, `--hora-fin`, `--ventana-dias` y `--capacidad-hora`.
- El mensaje de último intento ya no depende de una constante: el pipeline pasa `ultimo_intento` al generador de mensajes, que se agrega a los campos permitidos del contexto.

### Pruebas
- 64 pruebas (18 nuevas). Cubren reglas inválidas, no contactar antes de las 10:00, quitar el sábado, máximo de 2 intentos (excluye a quien ya tiene dos y cambia el mensaje a último intento), ventana más corta, capacidad de 8 por hora, 72 h entre intentos y validez de los mensajes con reglas distintas a las de defecto.
- Verificación de la interfaz con `AppTest`: cambia el número de leads al mover los controles y muestra el error al quitar todos los días.

## 0.1.0 (23-nov-2026)

### Datos (`data.py`)
- Se normalizan dos formatos de `fecha_registro` y `primer_contacto` (`YYYY-MM-DD HH:MM` y `DD/MM/YYYY HH:MM`). 109 filas venían en el segundo. Un formato desconocido lanza error en lugar de ignorarse.
- La columna `estado` se renombra a `entidad` para no confundirla con el resultado del lead.
- Edades menores de 18 o mayores de 100 pasan a nulo y se marcan (`edad_valida`): 14 filas.
- Se marcan 70 teléfonos repetidos (`es_duplicado`), conservando el primer registro por fecha.
- Las banderas `ya_es_cliente`, `telefono_rechazo` y `telefono_en_seguimiento` se calculan por teléfono y se propagan a todos sus registros. Motivo: en 3 casos el original ya había comprado y su re-registro seguía figurando como lead abierto.
- `intentos_previos` y `ultimo_contacto` se calculan por teléfono.

### Variables (`features.py`)
- Franja horaria del contacto, rango de espera desde el registro, día de la semana, canal, objetivo, edad y plan.
- El objetivo de predicción es que la persona conteste (`resultado` distinto de `no_contesta`) entre los leads con primer contacto y sin duplicados.
- Para programar horarios futuros se fija la espera en 18 h, porque el modelo solo observó primeros contactos de hasta 48 h.

### Modelo (`model.py`, `evaluation.py`)
- Regresión logística con codificación one-hot y escalado de numéricas. Árbol potenciado como comparación.
- Evaluación hacia adelante en el tiempo: entrenamiento con leads anteriores al 25-oct (1,066) y prueba con los posteriores (558).
- Resultados en prueba: AUC 0.603 (IC 95%: 0.549 a 0.647) la logística, 0.599 el árbol, 0.500 la tasa constante. Brier 0.227, 0.230 y 0.233. Se conserva la logística por igualdad de desempeño y porque permite explicar cada recomendación.
- Las contribuciones por variable se calculan desde los coeficientes. Una prueba comprueba que su suma es igual a la diferencia en logit contra el promedio de entrenamiento.
- Ablación por familias de variables (AUC): solo canal 0.601, horario y canal 0.616, solo espera 0.575, solo horario 0.572, espera y horario 0.577, perfil 0.501, todo 0.603.
- Hallazgo: el horario y la espera aportan casi la misma señal. Casi todos los contactos de 13 a 18 h ocurrieron a menos de 2 h del registro, así que el efecto del horario no es separable con estos datos.
- Hallazgo: la calibración subestima en los grupos de probabilidad baja durante el periodo de prueba (predicha 0.44, observada 0.52 en el grupo más bajo).

### Reglas de trato (`policy.py`, `config.py`)
- Horario 9:00 a 20:00 de lunes a sábado, máximo 3 intentos, 24 h entre intentos, ventana de recuperación de 21 días.
- Se excluyen clientes, rechazos, personas en seguimiento y registros repetidos. Cada exclusión queda con un motivo legible.
- La ventana, el máximo de intentos y el tiempo entre intentos son supuestos, no datos.

### Asignación de horarios (`pipeline.py`)
- Primera versión: cada persona recibía su horario de mayor probabilidad. Resultado: 291 personas asignadas al mismo martes a las 13:00, imposible de atender.
- Corrección: límite de contactos por hora (15 por defecto) y asignación en orden de prioridad. Los nunca contactados van primero y en la primera hora con espacio; el resto elige su mejor horario libre. Quien no encuentra espacio queda en cola, no se descarta.
- Resultado: máximo de 15 contactos por hora, 55 nunca contactados el primer día y 346 asignados en 4 días.
- El orden de prioridad es: nunca contactado, mayor tiempo desde el registro, mayor probabilidad. La probabilidad no excluye a nadie.

### Mensajes (`mensajes.py`, `llm.py`)
- Tres plantillas: primer contacto, segundo intento y último intento. Todas incluyen la opción de baja y la marca.
- Validador que rechaza menciones de la condición de salud, promesas de resultados, urgencia, enlaces, mensajes sin opción de baja o sin marca, y textos de más de 480 caracteres.
- El contexto que puede llegar al LLM está limitado a intento, contacto previo, franja del día y asesor. Cualquier otro campo lanza error.
- Cliente opcional de la API de Anthropic con `urllib`, sin dependencias nuevas. Si no hay llave, falla la red o el texto no pasa el validador, se usa la plantilla.
- La conexión con la API no se probó contra el servicio real; sí con un cliente simulado.

### Interfaz (`app/streamlit_app.py`)
- Cuatro pestañas: lista del día, reglas de trato, modelo y evidencia, límites y plan de prueba.
- Controles de fecha y de capacidad por hora. Descarga de la lista en CSV.
- Verificada con `streamlit.testing.v1.AppTest`: sin excepciones al cargar, al cambiar la capacidad y al filtrar.

### Pruebas
- 46 pruebas en `tests/`: limpieza de datos, reglas de exclusión, horarios, validador y respaldo de mensajes, ausencia de datos personales en el prompt, no mezcla entre entrenamiento y prueba, límites de capacidad, determinismo de la lista y explicación del modelo.

### Pendiente técnico
- Ninguna medición del efecto real del horario ni del mensaje: los datos solo tienen un intento por lead.
