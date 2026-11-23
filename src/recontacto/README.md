# `src/recontacto/` · lógica en Python

Paquete con toda la lógica: datos, reglas de trato, modelo, mensajes, lectura de respuestas, ingesta, simulación y control estadístico. No depende de la interfaz: la usan la aplicación Dash, los scripts, los `.bat` y las pruebas.

| Módulo | Qué hace | Dónde cambiar |
|---|---|---|
| `config.py` | Rutas, reglas de trato por defecto (`Reglas`), marca | Valores por defecto de las reglas |
| `data.py` | Limpieza de datos y bajas | Formatos de fecha y banderas por teléfono |
| `ingesta/` | Leer, validar, fusionar y versionar datos de cualquier fuente | Tabla de archivos en `docs/ARQUITECTURA.md` |
| `features.py`, `model.py`, `evaluation.py` | Variables, regresión logística y evaluación hacia adelante | Variables del modelo |
| `policy.py` | Reglas de exclusión: ventana, intentos, clientes, rechazos, bajas | Una regla nueva |
| `pipeline.py` | Lista priorizada con horario, límite por hora y mensaje | Prioridad y asignación |
| `mensajes.py` | Biblioteca por situación, variantes y validadores | `BIBLIOTECA`, `ESTRATEGIAS`, `validar_mensaje` |
| `llm.py` | Clientes opcionales de modelos de lenguaje (con respaldo en plantillas) | Modelo y prompt |
| `respuestas.py` | Lee lo que contesta la persona y decide qué hacer | `ACCIONES` y el orden de prioridad |
| `simulacion.py`, `control.py` | Monte Carlo, prueba A/B, intervalos, carta p, variantes | Parámetros de simulación |
| `visibilidad.py` | Panel de visibilidad en IA | Patrones de encuadre |
| `cli.py` | Lista del día desde la línea de comandos | Opciones |

Convención: cada módulo abre con un docstring que dice qué hace y **dónde cambiar cosas**. Ver [`docs/CONTRIBUIR.md`](../../docs/CONTRIBUIR.md).
