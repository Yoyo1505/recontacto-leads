# Guía de operación

Para quien opera la herramienta día a día. Todo se puede hacer con doble clic en los archivos de `bat/` (el más cómodo es `bat\menu.bat`) o con los comandos equivalentes. Los comandos suponen que se corren desde la carpeta del proyecto con `set PYTHONPATH=src` (los `.bat` ya lo hacen).

## Requisitos

- Python 3.11 o superior y `pip install -r requirements.txt` (o `bat\instalar.bat`).
- Node.js solo para comprobar la versión web contra Python y para las pruebas completas.
- Google Chrome solo para grabar el video y para `verificar_web.py`.
- Nube o bases de datos de red: `bat\instalar_nube_y_bases.bat` (instala solo lo que haga falta).

## Rutina diaria

| Paso | Qué hacer | Comando |
|---|---|---|
| 1 | Actualizar los datos del CRM | `bat\actualizar_datos.bat archivo` o `bat\actualizar_desde_base.bat tabla` |
| 2 | Revisar el informe: filas rechazadas, avisos y conflictos. **No se guarda nada hasta aplicar** | (el mismo comando, sin `--aplicar`) |
| 3 | Aplicar si el informe es correcto | `python -m recontacto.ingesta --origen ... --aplicar` |
| 4 | Registrar las bajas del día | `bat\registrar_baja.bat 5512345678` |
| 5 | Generar la lista del día | `bat\lista_del_dia.bat [fecha]` → `outputs/` |
| 6 | Revisar la lista y enviar los mensajes (el asesor los envía; la herramienta no envía) | Aplicación: `bat\iniciar_app.bat` |
| 7 | Anotar las respuestas | Sección Respuestas o `python -m recontacto.respuestas --texto "..." --lead L00001 --aplicar` |

## Qué mirar en el informe de datos

| Señal | Qué significa | Qué hacer |
|---|---|---|
| Muchas filas rechazadas con el mismo motivo | Cambió el formato de la fuente (fechas, teléfonos, columnas) | No aplicar; corregir la fuente o agregar el sinónimo en `ingesta/esquema.py` |
| Conflictos | Un `lead_id` ya existe con otro teléfono | Revisar con el CRM; no se aplica el cambio |
| Avisos de "venta sin monto" o "primer contacto anterior al registro" | Datos inconsistentes, no bloquean | Revisar con quien captura |
| Columnas ignoradas | La fuente trae columnas desconocidas | Confirmar que no sea una columna que sí se necesita |

## Bajas: la regla más importante

Quien pide no recibir mensajes **no se vuelve a contactar**, venga el dato de donde venga. Una baja se registra por teléfono (normalizado) en `data/bajas.csv` y excluye al lead de toda lista futura, aun si llega en archivos nuevos. Al registrarla, avisar también al CRM y al canal: hoy esa lista no se sincroniza sola (ver `ANALISIS_PENDIENTES.md`, P0-3).

## Volver atrás

| Situación | Comando |
|---|---|
| Ver versiones guardadas | `python -m recontacto.ingesta --listar-versiones` |
| Volver a la última versión | `bat\restaurar_datos.bat` |
| Volver a una versión | `bat\restaurar_datos.bat leads_20261123_101500_000000.csv` |
| Volver a la base original | `bat\restaurar_datos.bat original` |

Restaurar también guarda una copia de la base que se reemplaza. Se conservan 20 versiones (`config.VERSIONES_A_CONSERVAR`).

## Versión web

| Tarea | Comando |
|---|---|
| Regenerar la página tras cambiar datos, modelo o código web | `bat\construir_web.bat` (exporta desde Python, ensambla, arma y compara contra Python) |
| Abrirla localmente | `bat\abrir_version_web.bat` |
| Comprobar que JavaScript da lo mismo que Python | `node web\prueba_motor.js` |
| Comprobar la página en un Chrome real | `python scripts\verificar_web.py [url]` |
| Revisar el formato en pantalla dividida y en teléfono | `python scripts\revisar_responsivo.py [--capturas carpeta]` |
| Publicar | Copiar el contenido de `web\sitio\` (cinco páginas y `demo.mp4`) a la raíz del repositorio de la página |

## Lista de verificación antes de entregar una versión

1. `python -m pytest` pasa completo (229 pruebas o más).
2. `node web\prueba_motor.js` dice "coincide con Python".
3. `python scripts\ensamblar_web.py --revisar` no reporta nada desactualizado.
4. `python scripts\verificar_web.py` y `python scripts\revisar_responsivo.py` terminan en "todo bien".
5. `CHANGELOG.md` tiene la entrada de la versión y `pyproject.toml` el número nuevo.
6. No hay datos reales en el repositorio (`git status` y revisar `data/`).
7. Si cambiaron las pantallas: regrabar el video (`bat\crear_video.bat`, con la aplicación corriendo) y el GIF.

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| "No se encontró Python" | Python no está en el PATH | Instalar Python 3.11+ y marcar "Add to PATH" |
| La lista sale vacía | Todos los leads excluidos por reglas (ventana, intentos, bajas) | Revisar los motivos de exclusión en la sección Lista y la fecha de la lista |
| "Faltan columnas obligatorias" | La fuente no trae `lead_id`, `fecha_registro`, `canal`, `telefono` o `resultado` | Agregar el sinónimo en `ingesta/esquema.py` o renombrar en la fuente |
| La app Dash muestra datos viejos | La caché no se recargó | Reiniciar la aplicación; tras aplicar datos desde la sección Datos se recarga sola |
| La web y Python difieren | Datos o modelo exportados desactualizados | `bat\construir_web.bat` |
| `ensamblar_web.py --revisar` falla | Se editó `web/motor.js` o `web/app.js` a mano | Pasar el cambio a `web/fuente/` y correr `ensamblar_web.py` |
| Error al leer de una base | Falta el conector o la cadena es incorrecta | `bat\instalar_nube_y_bases.bat`; las contraseñas nunca se muestran en el mensaje |
| El video no se graba | Chrome no está en la ruta por defecto | Definir `CHROME_EXE` con la ruta de `chrome.exe` |
