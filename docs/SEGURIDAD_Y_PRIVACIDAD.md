# Seguridad y privacidad

Qué protege hoy la herramienta, qué no, y qué debe resolverse antes de usar datos reales. **Esto no es asesoría legal**: los puntos legales son preguntas para el área jurídica, no conclusiones.

## Qué datos maneja

| Dato | Dónde aparece | Sensibilidad |
|---|---|---|
| Teléfono | `telefono` en leads y `bajas.csv` | Dato personal que identifica a la persona |
| Objetivo de salud (`objetivo`: "diabetes tipo 2", "control de peso") | leads | Dato de salud: se trata como sensible |
| Edad, estado, canal, plan de interés | leads | Dato personal |
| Resultado de contacto y monto de venta | leads | Dato comercial |

Los datos del repositorio (`data/leads_ficticios.csv`) son **ficticios**. El repositorio público no debe contener nunca datos reales.

## Qué protege hoy

| Control | Dónde |
|---|---|
| Ningún mensaje menciona la condición de salud, promete resultados, mete urgencia ni lleva enlaces; todo mensaje trae la forma de darse de baja | `mensajes.validar_mensaje` (aplica también a los mensajes de un modelo de lenguaje) |
| Al modelo de lenguaje solo llegan intento, franja del día, asesor, variante y origen; cualquier otro campo lanza error. **No recibe el teléfono ni el objetivo de salud** | `mensajes._verificar_contexto` |
| Las bajas se respetan por teléfono normalizado, aun en archivos futuros | `data.leer_bajas`, `policy` |
| Una baja o una urgencia se detecta antes que cualquier otra intención en una respuesta | `respuestas.clasificar` |
| Las cadenas de conexión se enmascaran (usuario, contraseña, tokens) en mensajes de error, informes y registros | `ingesta.enmascarar` |
| Las bases SQL se leen en solo lectura: un solo `SELECT` sin `;` ni instrucciones que modifiquen datos, y nombres de tabla validados | `ingesta/lectura.py` |
| Las credenciales de la nube van en variables de entorno, nunca en el comando | `ingesta/lectura.py` |
| La llave de la API de Anthropic se lee de `ANTHROPIC_API_KEY`; no se escribe en archivos | `llm.py` |
| Nada se borra: toda actualización guarda una copia y se puede restaurar | `ingesta/versiones.py` |
| Un archivo mal formado no cambia nada: primero informe, luego aplicar | `ingesta/fusion.py` |
| `.gitignore` excluye `data/leads_actual.csv`, `bajas.csv`, `data/historial/` y `outputs/` | `.gitignore` |
| En la versión web, los datos no salen del navegador: no hay servidor ni llamadas de red con datos (solo se cargan librerías públicas) | `web/` |

## Qué no protege todavía

| Brecha | Detalle | Pendiente |
|---|---|---|
| Sin autenticación | La aplicación Dash no pide inicio de sesión: quien llegue a la dirección ve todo | P0-4 |
| Sin auditoría | No queda registro de quién aplicó datos, restauró o registró una baja | P0-4 |
| Bajas no sincronizadas | `bajas.csv` (Python) y el navegador (web) no se comparten ni con el CRM | P0-3 |
| Datos en reposo sin cifrar | Los CSV están en disco sin cifrado; depende del disco de la computadora | P1-6 |
| Librerías de la página web desde internet | La página carga Plotly, PapaParse y SheetJS desde una CDN pública (versión fija); un compromiso de la CDN afectaría la página | Empaquetar las librerías o usar integridad de subrecursos (SRI) |
| Dependencias sin versión fija | `requirements.txt` no fija versiones | P1-4 |
| Mensajes sin revisión legal | Las 8 plantillas no las revisó el área jurídica | P0-1 |

## Preguntas para el área jurídica (antes de usar datos reales)

1. ¿Cuál es la base legal y el aviso de privacidad vigente para recontactar a quien solicitó información? ¿Cubre el recontacto por WhatsApp?
2. Los datos de salud, ¿requieren consentimiento expreso para esta finalidad?
3. ¿Cuánto tiempo pueden conservarse los datos de quien no contestó o pidió la baja? (La ventana técnica es de 21 días; la retención es otra cosa.)
4. ¿Cómo se atienden los derechos de acceso, rectificación, cancelación y oposición sobre la lista de bajas y el historial?
5. ¿Qué dicen las plantillas aprobadas del canal sobre el contenido permitido?
6. Los modelos de lenguaje de terceros, ¿pueden recibir algún dato del lead? (Hoy no reciben teléfono ni salud.)

## Si se sospecha una fuga

1. Dejar de usar la herramienta y desconectar la computadora o el servicio de la red.
2. Avisar al responsable de seguridad y a jurídico; no borrar nada (el historial sirve para investigar).
3. Cambiar las credenciales que se hayan usado (cadenas de conexión, `ANTHROPIC_API_KEY`, tokens).
4. Si el repositorio público recibió datos reales: pedir a GitHub que elimine los commits afectados, rotar cualquier secreto y asumir que los datos ya se copiaron.

## Cómo reportar un problema

Abrir un issue en el repositorio **sin incluir datos personales**; para un problema de seguridad, avisar directamente al responsable del proyecto.
