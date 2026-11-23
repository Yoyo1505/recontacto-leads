# Documentación del proyecto

Índice de la documentación. La aplicación está en Dash y dividida en secciones independientes para que cada cambio toque un solo archivo.

| Documento | Contenido |
|---|---|
| [`../README.md`](../README.md) | Resumen, resultados y cómo correr el proyecto |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Registro de cambios por versión |
| [`bitacora.md`](bitacora.md) | Bitácora técnica: decisiones, errores y su corrección |
| [`ANALISIS_PENDIENTES.md`](ANALISIS_PENDIENTES.md) | Qué falta para producción, por prioridad |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Módulos, flujo de datos y decisiones de diseño |
| [`OPERACION.md`](OPERACION.md) | Guía de operación: rutina diaria, volver atrás, problemas frecuentes |
| [`SEGURIDAD_Y_PRIVACIDAD.md`](SEGURIDAD_Y_PRIVACIDAD.md) | Qué protege hoy, qué no y qué preguntar a jurídico |
| [`CONTRIBUIR.md`](CONTRIBUIR.md) | Convenciones, recetas de cambio y pruebas |
| [`prueba_dos_personas.md`](prueba_dos_personas.md) | Guía y plantilla de la prueba con dos personas (pendiente de hacer) |
| [`investigacion_clivi.md`](investigacion_clivi.md) | Investigación de la empresa y de su visibilidad en IA y buscadores |
| [`plan_visibilidad_ia.md`](plan_visibilidad_ia.md) | Plan a 90 días para que las IA recomienden a Clivi como solución, no como alternativa |
| [`contenido_solucion_clivi.md`](contenido_solucion_clivi.md) | Ejemplo de `llms.txt` y páginas orientadas al problema del paciente |
| [`panel_visibilidad_prompts.csv`](panel_visibilidad_prompts.csv) | 36 preguntas de pacientes para medir la visibilidad (`python -m recontacto.visibilidad`) |
| [`experimento_recomendacion.md`](experimento_recomendacion.md) | Experimento con un modelo local: texto actual contra texto orientado a solución |
| [`prueba_llm_local.md`](prueba_llm_local.md) | Prueba de un modelo local como redactor de mensajes (seguridad y fidelidad) |
| Este archivo | Arquitectura, actualización de datos, recetas de cambio, reglas de trato y método de simulación |

## 1. Cómo correr

Todo se puede hacer con doble clic en los archivos de la carpeta `bat/` (el más cómodo es `bat\menu.bat`), o desde la línea de comandos:

```
set PYTHONPATH=src                (los .bat ya lo hacen solos)
python app/dash_app.py            abre http://127.0.0.1:8050
python app/dash_app.py --puerto 8060
python -m recontacto.cli          lista del día sin interfaz
python -m recontacto.ingesta ...  actualizar datos (ver sección 3)
python -m pytest                  todas las pruebas
python scripts/grabar_demo.py     regenera el GIF de la presentación
```

| Archivo en `bat/` | Qué hace |
|---|---|
| `menu.bat` | Menú con todo lo de abajo |
| `instalar.bat` | Instala las librerías del proyecto |
| `instalar_nube_y_bases.bat` | Instala, si hace falta, el soporte de S3, Google Cloud, Azure, PostgreSQL, MySQL o SQL Server |
| `iniciar_app.bat [puerto]` | Inicia la aplicación y la abre en el navegador |
| `lista_del_dia.bat [fecha]` | Genera la lista del día en `outputs/` |
| `simular_dos_personas.bat` | Muestra qué haría la herramienta con dos personas nuevas, sin guardar nada |
| `actualizar_datos.bat archivo` | Actualiza desde CSV, JSON, Excel, Parquet o SQLite |
| `actualizar_desde_base.bat tabla` | Actualiza desde una base SQL |
| `actualizar_desde_nube.bat url` | Actualiza desde una dirección web, S3, Google Cloud o Azure |
| `registrar_baja.bat telefono` | Registra a quien pidió no recibir mensajes |
| `restaurar_datos.bat [version\|original]` | Vuelve a una versión anterior de los datos |
| `evaluar.bat` | Recalcula las métricas y las figuras |
| `probar.bat` | Corre las pruebas |
| `abrir_version_web.bat` | Abre la versión web (no instala nada) |
| `construir_web.bat` | Regenera la versión web desde Python, ensambla las secciones y la compara con Python |
| `grabar_demo.bat` | Regraba el GIF (con la aplicación corriendo) |
| `crear_video.bat` | Crea el video MP4 de la presentación, con ejemplos de conversación (con la aplicación corriendo) |

## 2. Mapa de la aplicación

```
app/
  dash_app.py        ensambla: encabezado, barra lateral con reglas, menú y rutas
  contexto.py        datos, modelo y cálculos pesados en caché; se recarga tras actualizar datos
  tema.py            colores, tipografía y estilo común de las gráficas
  componentes.py     tarjeta, KPI, gráfica, columnas
  assets/            estilo.css y logo (Dash los sirve solos)
  secciones/
    resumen.py       portada: embudo y no contesta por canal
    lista.py         tabla, mapa de calor, detalle y descarga
    mensajes.py      biblioteca de mensajes por situación y variantes
    respuestas.py    qué entiende la herramienta de una respuesta
    evidencia.py     intervalos, confusión, variables, calibración, carta p, embudo de asesores
    simulacion.py    Monte Carlo con sensibilidad al supuesto alpha
    prueba_ab.py     tamaño de muestra, potencia y duración
    datos.py         subir archivos, agregar personas, bajas y versiones
    limites.py       lo que no se puede afirmar y los supuestos
src/recontacto/
  data.py            lectura, limpieza y banderas por teléfono (incluye la lista de bajas)
  ingesta/           paquete: esquema, utilidades, lectura, validación, fusión, versiones, simulación y cli
  features.py, model.py, policy.py, pipeline.py, mensajes.py, respuestas.py, llm.py
  simulacion.py, control.py, evaluation.py, visibilidad.py, cli.py
web/                 versión web: fuente/ (secciones de motor y de interfaz), motor.js y app.js (ensamblados), plantilla.html y estilos.css; entrega.html es el resultado
bat/                 archivos .bat para todo
data/
  leads_ficticios.csv    base original (nunca se modifica)
  leads_actual.csv       base vigente tras actualizar (se crea sola)
  historial/             copia de cada versión anterior
  bajas.csv              teléfonos que pidieron no recibir mensajes
  ejemplos/              dos personas nuevas en CSV, JSON, Excel y Parquet
```

Cada sección expone la misma interfaz (`ID`, `TITULO`, `RUTA`, `layout(ctx)`, `registrar(app, ctx)`) y su encabezado explica qué muestra, cómo leerla y dónde cambiarla. Las gráficas son funciones `figura_*` puras, que se prueban sin levantar el servidor.

## 3. Actualizar la información

### Qué pasa cuando llega una persona nueva

```
llega → se valida → se compara con la base (lead_id) → se le aplican las reglas de trato
      → se le asigna horario y mensaje, o se explica por qué hoy no se le escribe
```

Para verlo sin guardar nada: `bat\simular_dos_personas.bat` o la sección **Datos** de la aplicación. El ejemplo `data/ejemplos/dos_personas_nuevas.*` trae a una persona nunca contactada que llegó por un agente de IA y a otra que no contestó un primer intento. Resultado con los datos actuales: la primera se agenda el mismo día en la primera hora con espacio, con un mensaje de primer contacto; la segunda se agenda en el mejor horario disponible pasadas 24 horas de su intento, con un mensaje de segundo intento. Si alguna ya fuera cliente, hubiera pedido no recibir mensajes o repitiera un teléfono, se explica por qué no se le contacta.

### Formatos y fuentes

| Fuente | Cómo |
|---|---|
| CSV, JSON, JSON por líneas, Excel (`.xlsx`, `.xls`), Parquet | Ruta local, o arrastrar el archivo en la sección Datos |
| SQLite | Ruta del archivo `.db` (tabla `leads` por defecto) |
| Base SQL (PostgreSQL, MySQL, SQL Server, Oracle...) | Cadena de conexión en la variable `RECONTACTO_DB_URL` y `actualizar_desde_base.bat tabla` |
| Dirección web | `https://...` con `actualizar_desde_nube.bat` |
| S3, Google Cloud, Azure | `s3://`, `gs://`, `az://` tras instalar la librería con `instalar_nube_y_bases.bat` |

Columnas obligatorias: `lead_id`, `fecha_registro`, `canal`, `telefono`, `resultado`. Opcionales: `anuncio`, `estado` (entidad), `edad`, `objetivo`, `plan_de_interes`, `asesor`, `primer_contacto`, `monto_venta` y `baja`. Se aceptan sinónimos (por ejemplo `celular` o `whatsapp` en lugar de `telefono`, `fuente` en lugar de `canal`). Valores de `resultado`: `no_contesta`, `sin_contactar`, `en_seguimiento`, `no_interesado`, `venta`. Un canal nuevo (por ejemplo `Agente IA`) se acepta sin cambiar código.

### Garantías

- Nada se guarda sin confirmar. Primero se muestra el informe: filas leídas, válidas, rechazadas con su motivo, avisos, personas nuevas y actualizadas.
- Lo rechazado se guarda en `outputs/rechazados_*.csv` para revisarlo; nada se descarta en silencio.
- Se actualiza por `lead_id` y nunca se borra: quien no viene en un archivo nuevo se queda como estaba. Si un `lead_id` ya existe con otro teléfono, se rechaza como conflicto.
- La misma persona se reconoce aunque cambie el formato del teléfono (`+52 55 0152 1432` y `55-01521432`).
- Cada cambio guarda una copia de la versión anterior (se conservan las últimas 20). Restaurar también guarda la actual. La base original no se toca nunca.
- Subir dos veces el mismo archivo no cambia nada.

### Seguridad de las conexiones

- Las contraseñas y llaves van en variables de entorno, nunca en los `.bat`, en el comando ni en el repositorio. Las cadenas de conexión se enmascaran al mostrar errores.
- Las consultas a bases de datos son solo de lectura: un único `SELECT` sin instrucciones que modifiquen datos. Aun así conviene usar un usuario de la base con permiso solo de lectura.
- Ejemplos:
  ```
  setx RECONTACTO_DB_URL "postgresql://usuario:clave@servidor:5432/clivi"
  setx AWS_ACCESS_KEY_ID "..." & setx AWS_SECRET_ACCESS_KEY "..."
  ```
  (cierra y abre la ventana de comandos después de `setx`).
- Lo que no se probó: las conexiones reales a S3, Google Cloud, Azure, PostgreSQL y MySQL, porque no hay credenciales ni los conectores instalados aquí. Sí se probaron CSV, JSON, Excel, Parquet, SQLite, cadenas de conexión SQLAlchemy, descarga por HTTP y los mensajes de error cuando falta una librería.

### Quien pide no recibir mensajes

`bat\registrar_baja.bat telefono`, o la sección Datos. Se guarda en `data/bajas.csv` y se aplica a toda la base: esa persona no aparece en ninguna lista, ni siquiera si su teléfono llega otra vez en un archivo nuevo, y las bajas sobreviven a restaurar versiones. También se respeta una columna `baja` en los datos.

## 4. Recetas de cambio rápido

| Quiero | Dónde |
|---|---|
| Cambiar un color | `COLORES` en `app/tema.py` y las variables al inicio de `app/assets/estilo.css` |
| Cambiar el texto de la portada | `PORTADA` en `app/secciones/resumen.py` |
| Agregar una sección | Crear el módulo en `app/secciones/` con la interfaz común y añadirlo a `SECCIONES` en `secciones/__init__.py` |
| Quitar una sección | Borrarla de `SECCIONES` |
| Agregar o quitar una gráfica | Editar `layout` de la sección; si es dinámica, también `registrar` |
| Cambiar los valores por defecto de las reglas | `Reglas` en `src/recontacto/config.py` |
| Agregar un control a la barra lateral | `panel_reglas` y `reunir_estado` en `app/dash_app.py`, y el campo en `Reglas` |
| Agregar una regla de exclusión | `MOTIVOS` y `evaluar_elegibilidad` en `src/recontacto/policy.py` |
| Cambiar el orden de prioridad | `sort_values` en `calcular_asignacion`, `src/recontacto/pipeline.py` |
| Cambiar el texto de un mensaje | `plantilla` en `src/recontacto/mensajes.py` y su prueba |
| Agregar una variable al modelo | `features.py` (`CATEGORICAS` o `NUMERICAS` y `desde_contactos`) |
| Aceptar otro nombre de columna | `SINONIMOS` en `src/recontacto/ingesta.py` |
| Cambiar qué se valida de cada fila | `validar` en `src/recontacto/ingesta.py` |
| Agregar un canal | No requiere código: se toma de los datos |
| Cambiar el número de simulaciones del bootstrap | `N_BOOTSTRAP` en `app/contexto.py` |
| Cambiar los efectos de la prueba A/B | `EFECTOS` en `app/secciones/prueba_ab.py` |

Después de cualquier cambio: `bat\probar.bat`. La prueba `test_todos_los_callbacks_responden_sin_error` dispara cada callback y falla si se agrega uno sin valores de prueba.

## 5. Reglas de trato

Esta sección es solo documentación: describe qué reglas se aplican y por qué. La aplicación permite mover sus valores desde la barra lateral, pero no tiene una pantalla dedicada a explicarlas.

| Regla | Valor por defecto | Por qué | Dónde está |
|---|---|---|---|
| Horario de contacto | 9:00 a 20:00, de lunes a sábado | No escribir de madrugada ni en domingo | `Reglas.hora_inicio`, `hora_fin`, `dias_permitidos` |
| Máximo de intentos | 3 | Evitar insistir | `Reglas.max_intentos` |
| Tiempo entre intentos | 24 h | Dar espacio entre mensajes | `Reglas.horas_entre_intentos` |
| Ventana de recuperación | 21 días desde el registro | Pasado ese tiempo, el interés probablemente cambió | `Reglas.ventana_dias` |
| No contactar | Quien pidió no recibir mensajes, clientes, quien dijo que no le interesa, quien ya habla con un asesor, registros repetidos | Respeto y evitar confusión | `policy.evaluar_elegibilidad` |
| Capacidad | 15 contactos por hora | Que el equipo pueda atender la lista | `Reglas.capacidad_por_hora` |
| Privacidad | Los mensajes no mencionan la condición de salud. El LLM solo recibe intento, franja del día y asesor | Datos sensibles | `mensajes.py` (`CAMPOS_PERMITIDOS`, `PATRONES_PROHIBIDOS`) |
| Baja | Todo mensaje trae la opción de no recibir más, y las bajas se respetan siempre | Control de la persona | `mensajes.validar_mensaje`, `data/bajas.csv` |
| Último intento | El tercer mensaje avisa que no se insistirá más | Nadie nos debe una respuesta | `mensajes.plantilla` |
| Equidad | El modelo elige el horario, no a quién ignorar. Quien no cabe queda en cola | Nadie debe quedar fuera por una probabilidad baja | `pipeline.calcular_asignacion` |

Los valores de horario, intentos, tiempo entre intentos, ventana y capacidad son supuestos, no datos.

## 6. Simulación y control estadístico

Detalle completo en los encabezados de `src/recontacto/simulacion.py` y `src/recontacto/control.py`.

- Simulación: se reentrena el modelo sobre remuestras bootstrap (incertidumbre del modelo) y se sortea quién contesta (azar del muestreo). Se compara el horario asignado contra un horario sin optimizar.
- Supuesto clave `alpha`: en los datos, la hora y la rapidez del contacto están mezcladas, así que se desconoce qué fracción de la ventaja del horario es causal. La simulación lo recorre de 0 a 1.
- Prueba A/B: prueba z de dos proporciones; tamaño de muestra analítico contrastado con simulación, y control del error tipo I.
- Control: intervalos de Wilson, carta p diaria (3 sigmas) y gráfico de embudo por asesor (95% y 99.8%).

## 7. Identidad visual

Colores, tipografía y logo extraídos del sitio público de Clivi; ver `investigacion_clivi.md`. El logo es marca de Clivi y se usa solo en este demo.

## 8. Limitaciones técnicas conocidas

- `dash_table.DataTable` quedará fuera de Dash en una versión mayor futura; la alternativa es `dash-ag-grid`.
- La aplicación guarda el archivo pendiente de aplicar en memoria del servidor: sirve para una persona usándola a la vez, no para varias sesiones simultáneas.
- Con datos nuevos, el modelo se vuelve a entrenar al recargar; si el periodo cambia mucho, la fecha de corte de la evaluación se ajusta sola.
- La conexión con la API de Anthropic para redactar mensajes está escrita pero no se probó contra el servicio real; sí con un cliente simulado.
- La búsqueda y los motores de IA no se consultaron para medir la visibilidad actual de Clivi; el protocolo para medirla está en `investigacion_clivi.md`.
