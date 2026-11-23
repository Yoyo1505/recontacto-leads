# Plan de entrega

Inicio: lunes 23-nov, 09:50. Cierre: martes 24-nov, aprox. 09:05 (23 h 15 min). Confirmar la hora exacta con quien convoca.

## 1. Qué hay que entregar y cuándo está "listo"

| Pieza | Está listo cuando | Estado |
|---|---|---|
| Herramienta | Corre con un comando, tiene demo guiada y se puede modificar en vivo en menos de 3 minutos | Base lista, falta pulir |
| Memo | 1 a 2 páginas solo sobre el proyecto: problema, solución, evidencia, límites, siguiente paso | Se escribe cuando los resultados queden finales |
| Bitácora | Registro técnico del proyecto, tipo changelog: cambios de código, datos y modelo, con su motivo técnico y su resultado. Sin planeación ni conversaciones | Primera versión escrita en `docs/bitacora.md`; se actualiza con cada cambio |
| Video demo | Grabado, de 4 a 5 minutos (confirmar duración pedida), con guion ensayado | Por grabar |
| Prueba con dos personas | Dos sesiones hechas, hallazgos anotados y al menos 2 mejoras aplicadas | Por agendar hoy |

## 2. Calendario

| Horario | Bloque | Salida |
|---|---|---|
| 09:50 a 10:30 | Alcance e ideas | Ideas del usuario priorizadas; dos personas para la prueba contactadas |
| 10:30 a 14:30 | Herramienta lista para demo | Reglas ajustables desde la interfaz, ruta de demo de 5 pasos, comando único, pruebas verdes |
| 14:30 a 15:30 | Comida y descanso | |
| 15:30 a 17:30 | Prueba con dos personas | Dos sesiones de 25 min con guion, notas y citas |
| 17:30 a 19:00 | Aplicar hallazgos | Dos mejoras hechas y registradas |
| 19:00 a 20:30 | Memo y bitácora | Versiones finales |
| 20:30 a 21:30 | Video demo | Grabación con dos tomas |
| 21:30 a 22:30 | Ensayo de la videollamada | Demo, 8 preguntas, 3 cambios en vivo |
| 22:30 a 06:30 | Dormir | |
| 06:30 a 08:00 | Revisión final y empaquetado | Entrega lista y probada en limpio |
| 08:00 a 09:05 | Margen | No se programa nada nuevo |

Si algo se atrasa, se recorta de la lista de la sección 6, nunca el sueño ni el margen final.

## 3. Reparto

Claude: ajustes a la herramienta, borradores de memo y bitácora, guion del video, guion y formulario de la prueba, banco de preguntas y cambios en vivo, revisión de consistencia entre piezas.

Usuario: aportar las ideas, conseguir y atender a las dos personas, grabar el video, aportar la trayectoria personal, decidir el tono y aprobar cada pieza.

## 4. Videollamada de 30 minutos

| Minutos | Parte |
|---|---|
| 0 a 2 | Qué problema, para quién y qué decidí |
| 2 a 10 | Demo en 5 pasos: lista del día, un lead con su motivo y mensaje, reglas de trato, evidencia del modelo, límites |
| 10 a 20 | Preguntas |
| 20 a 28 | Cambio en el momento |
| 28 a 30 | Cierre: qué haría con una semana más |

Preguntas probables y la respuesta corta:

1. ¿Por qué un AUC de 0.60 sirve? Mejora a la tasa constante con intervalo que excluye 0.5; se presenta como hipótesis y la prueba A/B lo confirma.
2. ¿Por qué regresión logística? Rinde igual que el árbol y cada recomendación se explica.
3. ¿Por qué no descartar a quien tiene baja probabilidad? Nadie nos debe una respuesta; el modelo elige el horario, no a quién ignorar.
4. ¿Cómo se protege la información de salud? Los mensajes no mencionan la condición y el LLM no recibe teléfono ni edad.
5. ¿Qué pasa si el LLM falla o escribe algo indebido? Validador y plantilla de respaldo.
6. ¿El horario importa de verdad? No se puede separar de la rapidez del contacto con estos datos; por eso la prueba.
7. ¿Cómo medirías el éxito? Porcentaje que contesta en 48 h y porcentaje que pide la baja.
8. ¿Qué harías con más datos? Segundos intentos, mensaje usado y hora de apertura.

Cambios en vivo para ensayar (cada uno en menos de 3 minutos, con su prueba):

| Cambio probable | Dónde |
|---|---|
| Máximo 2 intentos | `MAX_INTENTOS` o control en la interfaz |
| No llamar antes de las 10:00 | `HORAS_PERMITIDAS` |
| Quitar el sábado | `DIAS_PERMITIDOS` |
| Capacidad de 8 por hora | control en la interfaz |
| Mensaje más corto o de otro tono | `plantilla` en `mensajes.py` y su prueba |
| No contactar a menores de 18 | regla nueva en `policy.py` |
| Priorizar Referido | clave de orden en `pipeline.py` |
| Agregar una variable al modelo | `features.py` y re-evaluar |

## 5. Trayectoria y decisiones (30 minutos)

Estructura sugerida:

1. 0 a 5: quién eres y hacia dónde vas (aportar el usuario).
2. 5 a 12: trayectoria y qué la conecta con este proyecto: finanzas, Python y modelos con datos (tesis de SOFIPOs).
3. 12 a 25: decisiones del proyecto con su porqué, regresión logística, reglas de trato, plantillas antes que LLM, el límite de contactos por hora, el hallazgo de la confusión entre horario y espera.
4. 25 a 30: qué aprendiste y qué cambiarías.

Para el bloque 3 se usan las decisiones técnicas de la bitácora y del README; la bitácora en sí no incluye nada de este plan.

## 6. Qué se recorta si falta tiempo (en este orden)

1. Mejoras visuales de la interfaz.
2. Segunda toma del video.
3. Cambios en vivo menos probables.
4. Gráficas adicionales.

No se recorta: la prueba con dos personas, la honestidad sobre los límites ni el ensayo.

## 7. Riesgos

| Riesgo | Respuesta |
|---|---|
| No conseguir las dos personas a tiempo | Pedirlas ahora, con plan B de personas cercanas que hagan el rol de asesor |
| El LLM no está disponible en la llamada | Funciona con plantillas; se dice abiertamente |
| Falla la conexión durante la demo | Video grabado y capturas como respaldo |
| Un cambio en vivo rompe algo | Pruebas automáticas rápidas y un punto de control en git antes de la llamada |
| Contradicción entre piezas | Revisión cruzada de cifras en el bloque final |
