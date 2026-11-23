# Análisis de lo que falta para producción

Fecha: 23-nov-2026 · Versión analizada: 0.7.0

Este documento responde una pregunta: **si esto fuera a usarse mañana con personas reales, ¿qué falta?** Separa lo que está hecho y verificado, lo que está hecho pero no probado fuera de un entorno ficticio, y lo que no existe. Cada pendiente tiene prioridad, esfuerzo estimado y criterio de terminado.

Escala de prioridad: **P0** bloquea cualquier uso con datos reales · **P1** necesario para operarlo con confianza · **P2** mejora importante · **P3** deseable.
Escala de esfuerzo: **S** menos de un día · **M** de uno a cinco días · **L** más de cinco días o depende de otras personas.

## 1. Estado actual

| Área | Estado | Cómo se verificó |
|---|---|---|
| Limpieza de datos, reglas de trato, horarios y lista del día | Hecho | 229 pruebas automáticas en Python |
| Mensajes por situación (3 pasos, variantes A/B/C), validador de seguridad y de fidelidad | Hecho | Pruebas; las 8 plantillas pasan ambos validadores |
| Lectura de respuestas (baja, interés, cita, pregunta, malestar) | Hecho, solo con ejemplos escritos por el autor | 35 casos comparados entre Python y JavaScript |
| Versión web que abre sin instalar nada | Hecho | `node web/prueba_motor.js` (346 leads idénticos a Python) y 38 comprobaciones en Chrome real |
| Aplicación Dash por secciones (9) | Hecho | Pruebas de cada sección y de todos los callbacks |
| Carga de datos (CSV, JSON, Excel, Parquet, SQLite, bases SQL, URL, nube) | CSV, JSON, Excel, Parquet y SQLite probados; bases SQL de red y nube probadas solo con simulaciones | Pruebas con archivos reales y con `fsspec` en memoria |
| Modelo de lenguaje como redactor | Opcional y con respaldo en plantillas | Con llama3.1:8b local, 5 de 12 mensajes pasaron ambos validadores; la API de Anthropic no se probó contra el servicio real |
| Medición de variantes | Código listo (`control.comparar_variantes`), sin datos | Pruebas con datos sintéticos |
| Plan de visibilidad en IA y panel de medición | Plan y panel listos; sin medición real | Pruebas del panel; no se consultaron ChatGPT, Perplexity ni Google |
| Prueba con dos personas | **No hecha** | Guía en `prueba_dos_personas.md` |

## 2. Qué falta, por prioridad

### P0 · Antes de usar datos reales de personas

| # | Pendiente | Por qué importa | Esfuerzo | Criterio de terminado |
|---|---|---|---|---|
| P0-1 | **Privacidad y base legal.** Los leads incluyen teléfono y el objetivo de salud ("diabetes tipo 2"). En México los datos de salud se consideran sensibles (Ley Federal de Protección de Datos Personales en Posesión de los Particulares). No lo verifiqué con un abogado | Un uso sin aviso de privacidad ni consentimiento adecuado es un riesgo legal para la empresa | L (legal) | Revisión de legal: aviso de privacidad, finalidad "recontacto", plazo de conservación, derechos ARCO |
| P0-2 | **Consentimiento y canal.** Escribir por WhatsApp Business exige que la persona haya aceptado ser contactada y plantillas de mensaje aprobadas por la plataforma. No lo verifiqué | Mensajes sin consentimiento dañan el trato (el objetivo de la misión) y pueden bloquear la cuenta | M | Confirmar con el equipo de WhatsApp/CRM: prueba de consentimiento por lead y plantillas aprobadas (las 8 de la biblioteca como punto de partida) |
| P0-3 | **Bajas en un solo lugar.** Hoy viven en `data/bajas.csv` (Python) y en el navegador (web). No se comparten entre sí ni con el CRM | Una baja que no llega a todos lados es el peor fallo posible de esta herramienta | M | Una única lista de bajas (tabla o servicio) que lean la lista del día, el CRM y el canal; prueba de que una baja registrada en un lugar bloquea el mensaje en los demás |
| P0-4 | **Control de acceso y auditoría.** La aplicación Dash no tiene inicio de sesión ni roles; no queda registro de quién aplicó datos o registró una baja | Datos personales sin control de quién los ve ni qué hizo | M | Autenticación (SSO de la empresa o proxy con login), roles (asesor, supervisor, administrador) y un registro de auditoría de aplicar, restaurar y bajas |
| P0-5 | **Datos reales no deben ir al repositorio público.** El repositorio de GitHub es público y contiene solo datos ficticios | Subir leads reales por error expondría datos personales | S | `.gitignore` ya excluye `data/leads_actual.csv`, `bajas.csv` e `historial/`; falta una prueba en CI que falle si aparece un CSV con teléfonos reales (por ejemplo, formato distinto del ficticio) y un repositorio privado para el despliegue |

### P1 · Para operarlo con confianza

| # | Pendiente | Esfuerzo | Criterio de terminado |
|---|---|---|---|
| P1-1 | **Integración con CRM y canal.** Hoy la herramienta no envía mensajes ni recibe respuestas; las respuestas se pegan a mano | L | Lectura automática de leads desde el CRM (`actualizar_desde_base` ya soporta SQL) y envío por la API del canal, con el asesor aprobando cada lote al inicio |
| P1-2 | **Ejecución diaria automática.** La lista se genera a mano | S | Tarea programada (Programador de tareas o cron) que ejecute `lista_del_dia`, guarde la salida y avise si falla |
| P1-3 | **Integración continua.** No hay CI: las 229 pruebas se corren a mano | S | Flujo de GitHub Actions con pruebas de Python, `node web/prueba_motor.js` y `ensamblar_web.py --revisar` (ya está el archivo `.github/workflows/ci.yml`; requiere que el token de GitHub permita flujos) |
| P1-4 | **Dependencias sin versión fija.** `requirements.txt` no fija versiones | S | Archivo de bloqueo (`pip-compile` o `uv lock`) y prueba en CI con esas versiones |
| P1-5 | **Registros y alertas.** No hay registros estructurados ni alertas | M | Registros en JSON de cada ejecución (leads leídos, rechazados, enviados, bajas), y alerta si la tasa de rechazo de datos o de bajas sube de un umbral |
| P1-6 | **Respaldo de `data/`.** Las versiones se guardan localmente (20) pero no hay copia externa | S | Copia diaria de `data/historial/` y `bajas.csv` a un almacenamiento de la empresa |
| P1-7 | **Despliegue.** Solo se corre en una computadora o como página estática | M | Contenedor (Dockerfile) o servicio gestionado, con la configuración por variables de entorno y sin datos dentro de la imagen |
| P1-8 | **Medir el efecto real.** No hay ningún experimento: el AUC es 0.60 y la simulación de un día no se distingue del azar | L | Prueba A/B con grupo de control (unas 4,100 personas por grupo para ver +3 puntos, unas 560 para +8) usando `control.comparar_variantes` y `simulacion.tamano_muestra` |
| P1-9 | **Prueba con dos personas.** Requerida por la entrega | S | Completar `prueba_dos_personas.md` con lo observado y el cambio hecho |

### P2 · Mejoras importantes

| # | Pendiente | Esfuerzo |
|---|---|---|
| P2-1 | **Reentrenamiento y monitoreo del modelo.** Entrena al abrir la aplicación; no hay versionado ni alerta de deriva. La versión web no reentrena | M |
| P2-2 | **Separar el efecto del horario del de la rapidez.** Con un intento por lead no se pueden separar; requiere asignar horarios al azar en una parte de los leads | M |
| P2-3 | **Rendimiento con más datos.** Dash carga todo en memoria y la web calcula en el navegador; con decenas de miles de leads habría que paginar o usar una base | M |
| P2-4 | **Accesibilidad.** No se hizo una auditoría WCAG de la web ni de Dash (contraste, teclado, lectores de pantalla) | M |
| P2-5 | **Pruebas de extremo a extremo en CI.** La verificación en Chrome real (`verificar_web.py`) corre local | M |
| P2-6 | **Lectura de respuestas más robusta.** Se probó con ejemplos del autor; con respuestas reales aparecerán casos no previstos (emojis, audios, otros idiomas) | M |
| P2-7 | **Advertencia de Dash.** `dash_table.DataTable` se retirará en una versión mayor; migrar a `dash-ag-grid` | S |

### P3 · Deseable

| # | Pendiente | Esfuerzo |
|---|---|---|
| P3-1 | Formato y análisis estático (por ejemplo `ruff`) y tipos en los módulos públicos | S |
| P3-2 | Pruebas unitarias del JavaScript por sección (hoy se prueba el conjunto contra Python) | M |
| P3-3 | Más idiomas o variantes regionales de los mensajes | M |
| P3-4 | Probar el redactor con un modelo de lenguaje más capaz y con la API real | S |

## 3. Visibilidad en IA (proyecto aparte)

Es un plan con acciones que dependen de Clivi (contenido, equipo médico, legal, prensa), no del código. Pendientes concretos en [`plan_visibilidad_ia.md`](plan_visibilidad_ia.md): hoja de hechos única, contenido por problema, credibilidad médica y la primera medición del panel con los motores comerciales. El experimento local mostró que de memoria un modelo no conoce a Clivi (0 de 10) y que con fuentes aparece casi siempre; no demostró que el formato orientado a solución mejore la recomendación.

## 4. Riesgos conocidos

| Riesgo | Probabilidad | Impacto | Mitigación actual | Mitigación que falta |
|---|---|---|---|---|
| Mensaje a alguien que pidió no recibirlos | Baja (bajas respetadas en cada lista) | Muy alto | Exclusión por teléfono normalizado, aun en archivos futuros | P0-3 |
| Mensaje que menciona salud o promete resultados | Baja | Alto | Validador de seguridad en cada mensaje, incluidos los de un modelo de lenguaje | Revisión de legal de las plantillas |
| Persona con un malestar tratada como lead | Baja | Muy alto | El clasificador de respuestas pone seguridad primero y remite a un asesor y al 911 | Capacitar al asesor; probar con respuestas reales |
| Datos mal cargados contaminan la base | Media | Medio | Informe previo, rechazos con motivo, versiones restaurables | P1-6 |
| Atribuir al modelo una mejora que es azar | Alta | Medio | La documentación lo dice; no se afirma efecto | P1-8 |
| Fuga de datos personales | Baja | Muy alto | Datos ficticios; secretos enmascarados; `.gitignore` | P0-1, P0-4, P0-5 |

## 5. Orden recomendado

1. P0-1 y P0-2 en paralelo (legal y canal), porque son los que tardan y no dependen del código.
2. P0-3 y P0-4 (bajas centralizadas, acceso y auditoría).
3. P1-3, P1-4, P1-2 (CI, dependencias, ejecución diaria): un día de trabajo en total.
4. P1-9 y P1-1 (prueba con personas y conexión con el CRM), con un asesor aprobando cada lote.
5. P1-8: con la herramienta conectada, correr la prueba A/B de variantes y del horario.
