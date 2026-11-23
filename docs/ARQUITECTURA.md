# Arquitectura

La herramienta existe en dos versiones que deben dar el mismo resultado: **Python** (completa: Dash, ingesta de cualquier fuente, reentrenamiento) y **web** (una sola página que abre sin instalar nada). La versión web se verifica contra Python en cada cambio.

## Vista general

```
datos (CSV, JSON, Excel, Parquet, SQL, nube)
        │
        ▼
 ingesta/  ── leer ─ normalizar ─ validar ─ fusionar ─ versionar ──► data/leads_actual.csv  (+ data/historial/, data/bajas.csv)
        │
        ▼
 data.py (limpieza) ─► features.py ─► model.py (regresión logística) ─► pipeline.py ◄── policy.py (reglas de trato)
                                                                            │
                                         mensajes.py (3 pasos, variantes A/B/C, validadores)
                                                                            ▼
                                                        lista del día (quién, cuándo, qué mensaje, por qué)
        respuestas.py (leer lo que contesta la persona) ─► baja, estado nuevo, asesor
        simulacion.py · control.py · evaluation.py ─► incertidumbre, prueba A/B, control estadístico
        visibilidad.py ─► panel de visibilidad en IA (aparte de la lista)

 app/ (Dash, 9 secciones)         web/ (JavaScript, 12 archivos de motor + 14 de interfaz)
```

## Paquete `src/recontacto/`

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `config.py` | Rutas, reglas de trato por defecto (`Reglas`), marca, constantes | — |
| `data.py` | Lectura y limpieza (dos formatos de fecha, teléfonos repetidos, edades imposibles), bajas | `config` |
| `ingesta/` | Paquete. Ver abajo | `config`, `data` |
| `features.py` | Variables del modelo (hora, espera, canal, etc.) | `data` |
| `model.py` | Regresión logística y árbol potenciado; explicación por variable | `features` |
| `evaluation.py` | Evaluación hacia adelante en el tiempo, intervalos, calibración | `model` |
| `policy.py` | Reglas de trato: horario, intentos, ventana, exclusiones | `config` |
| `pipeline.py` | Une todo: lista priorizada, horario con límite por hora, mensaje | `model`, `policy`, `mensajes` |
| `mensajes.py` | Biblioteca por situación, variantes, validadores (seguridad y fidelidad), prompt para el redactor | `config` |
| `llm.py` | Clientes opcionales (Anthropic y Ollama) con respaldo en plantillas | `mensajes` |
| `respuestas.py` | Clasificador de respuestas por reglas y acciones | `ingesta` (al aplicar) |
| `simulacion.py` | Monte Carlo, potencia y tamaño de muestra | `pipeline` |
| `control.py` | Intervalos de Wilson, carta p, embudo, comparación de variantes | — |
| `visibilidad.py` | Puntuación de respuestas de IA sobre la marca | `control` |
| `cli.py` | Lista del día sin interfaz | `pipeline` |

### Paquete `ingesta/`

| Archivo | Responsabilidad |
|---|---|
| `esquema.py` | Columnas, sinónimos, valores válidos, `ErrorIngesta`, `Informe` |
| `utilidades.py` | Ocultar secretos, convertir textos, fechas y números |
| `lectura.py` | Leer archivos, SQLite, bases SQL (solo lectura), URLs y nube |
| `validacion.py` | Renombrar sinónimos y validar fila por fila |
| `fusion.py` | Agregar y actualizar por `lead_id`; nunca borra |
| `versiones.py` | Guardar con copia, restaurar, listar y registrar bajas |
| `simulacion.py` | Qué haría la herramienta con las personas que llegan |
| `cli.py`, `__main__.py` | `python -m recontacto.ingesta` |
| `__init__.py` | Reexporta todo: el resto del código usa `from recontacto import ingesta` |

## Aplicación Dash `app/`

Una sección por archivo en `app/secciones/` con la misma interfaz (`ID`, `TITULO`, `RUTA`, `layout(ctx)`, `registrar(app, ctx)`). Agregar o quitar una sección es editar la lista `SECCIONES` de `secciones/__init__.py`. Secciones: resumen, lista, mensajes, respuestas, evidencia, simulación, prueba A/B, datos y límites. `contexto.py` mantiene datos, modelo y cálculos pesados en caché y los recarga tras actualizar datos.

## Versión web `web/`

```
web/fuente/motor/NN_*.js   12 archivos del motor (fechas, datos, reglas, probabilidad, asignación, mensajes, respuestas,
                           estadística, simulación, ingesta, exportaciones)
web/fuente/app/NN_*.js     14 archivos de la interfaz (estado, gráficas, armado, lista, evidencia, simulación, prueba A/B,
                           datos, mensajes, respuestas, límites, rutas, arranque)
        │  scripts/ensamblar_web.py  (une en orden)
        ▼
web/motor.js, web/app.js   archivos ensamblados (se versionan; no se editan a mano)
        │  scripts/construir_web.py  (+ plantilla.html, estilos.css, logo, datos.json, modelo.json, evidencia.json)
        ▼
web/entrega.html           una sola página; en GitHub Pages es index.html
```

`scripts/exportar_web.py` calcula con Python lo que la web necesita: datos, coeficientes del modelo y de 100 modelos bootstrap, evidencia, lista de referencia y casos de prueba. La web **no reentrena**: usa esos coeficientes.

## Verificación entre versiones

`node web/prueba_motor.js` compara JavaScript contra Python: orden, horario, probabilidad, motivo, mensaje, etapa y variante de cada lead, exclusiones, prueba A/B, simulación (con tolerancia), ingesta, bajas, plantillas, `crc32` y 35 respuestas. `scripts/verificar_web.py` recorre la página en un Chrome real.

## Datos y estado

| Archivo | Contenido | ¿Versionado en Git? |
|---|---|---|
| `data/leads_ficticios.csv` | Base original ficticia; nunca se modifica | Sí |
| `data/leads_actual.csv` | Base vigente tras actualizar | No |
| `data/historial/` | Copia de cada versión anterior (20 como máximo) | No |
| `data/bajas.csv` | Teléfonos que pidieron no recibir mensajes | No |
| `outputs/` | Listas del día y rechazados | No |

## Decisiones de diseño

- **La probabilidad no excluye a nadie.** Solo elige el horario; quien no cabe un día pasa a una cola.
- **La regresión logística, no un modelo más complejo.** AUC 0.603 contra 0.599 de un árbol potenciado; cada recomendación se puede explicar.
- **Dos validadores de mensajes.** Seguridad (qué no puede decir) y fidelidad (que diga lo que la situación pide). Un modelo de lenguaje solo reescribe si pasa ambos; si no, se usa la plantilla.
- **Seguridad antes que baja, baja antes que todo** en la lectura de respuestas. Ante la duda, un asesor.
- **Nada se borra y todo es restaurable.** La ingesta fusiona, guarda una copia y permite volver.
- **Secretos nunca en pantalla ni en archivos.** Las cadenas de conexión se enmascaran; las credenciales de la nube van en variables de entorno.
