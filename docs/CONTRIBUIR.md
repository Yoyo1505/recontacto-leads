# Guía para contribuir

## Convenciones

- **Idioma:** español en textos, documentación, nombres de módulos y mensajes. Los nombres técnicos de librerías se dejan como son.
- **Código sin comentarios en línea.** La explicación va en el docstring del módulo y de la función, y en la documentación. Los marcadores de sección de los archivos de `web/fuente/` (`// ---- nombre`) no son comentarios: definen las secciones.
- **Cada módulo abre con un docstring** que dice qué hace, cómo leerlo y **"Donde cambiar cosas"** (qué constante o función tocar para cada cambio típico).
- **Una cosa por archivo.** Si una sección crece más de unos 300 líneas o mezcla responsabilidades, se divide (ver `src/recontacto/ingesta/` como ejemplo).
- **Todo cambio de comportamiento lleva prueba.** Las pruebas de Python están en `tests/`; la comparación contra JavaScript, en `web/prueba_motor.js`.
- **Nada de datos reales** en el repositorio, ni en pruebas, ni en capturas.
- **Mensajes a personas:** pasan por `validar_mensaje` y `validar_fidelidad`. No se mencionan condiciones de salud, no se promete, no se presiona y siempre hay forma de darse de baja.

## Flujo de trabajo

1. Crear una rama desde `main`.
2. Hacer el cambio en el archivo de la sección correspondiente (ver recetas).
3. Correr `python -m pytest`, `node web/prueba_motor.js` y, si tocaste la web, `python scripts/construir_web.py` y `python scripts/verificar_web.py`.
4. Actualizar `CHANGELOG.md` (sección "Sin publicar") y, si cambió algo operativo, `docs/OPERACION.md`.
5. Abrir una solicitud de cambios que explique **qué cambia, por qué y cómo se verificó**.

## Recetas

| Quiero... | Toco... | Además... |
|---|---|---|
| Cambiar una regla de trato (horario, intentos, ventana, capacidad) | `config.Reglas` (valores por defecto) y `policy.py` si cambia la lógica | Repetir en `web/fuente/motor/00_cabecera.js` (`REGLAS`) y correr la prueba de JavaScript |
| Cambiar el texto de un mensaje | `mensajes.BIBLIOTECA` | Repetir en `web/fuente/motor/06_mensajes.js`; correr `validar` (las pruebas validan las 8 plantillas) |
| Agregar una variante de mensaje | `BIBLIOTECA` y `ESTRATEGIAS` de `mensajes.py` y su par en JavaScript | Revisar la prueba de fidelidad; la asignación cambia para todos (usa `crc32`) |
| Agregar una intención en las respuestas | `respuestas.py` (`ACCIONES` y orden de prioridad) y `web/fuente/motor/07_respuestas.js` | Agregar casos en `scripts/exportar_web.py` y `tests/test_respuestas.py` |
| Agregar una columna a la ingesta | `ingesta/esquema.py` (`COLUMNAS`, `SINONIMOS`) y `ingesta/validacion.py` | Probar con `data/ejemplos/` |
| Aceptar un nuevo formato de archivo o fuente | `ingesta/lectura.py` (`leer_bytes` o `leer_fuente`) | Prueba en `tests/test_ingesta.py` |
| Agregar una sección a la aplicación Dash | Crear `app/secciones/<nombre>.py` con la interfaz común y registrarla en `app/secciones/__init__.py` | Agregar sus ids a `_valores` en `tests/test_app.py` |
| Agregar una sección a la web | Nuevo archivo `web/fuente/app/NN_<nombre>.js` con su marca de sección, y `python scripts/ensamblar_web.py` | `scripts/verificar_web.py` para recorrerla |
| Cambiar los colores o la tipografía | `web/estilos.css` (variables `--steel`, etc.) y `app/assets/estilo.css` / `app/tema.py` | Fuente: `docs/investigacion_clivi.md` |
| Cambiar el texto del memo, la bitácora, los demos o la prueba con dos personas | `web/paginas/memo.html`, `bitacora.html` o `video.html` | `python scripts/construir_web.py` |
| Cambiar el encabezado, el menú o el pie de todas las páginas | `web/paginas/base.html` (y `ENTREGAS` en `scripts/construir_web.py`) | Reconstruir |
| Cambiar cómo se ve en pantallas angostas | Bloques `@media` de `web/estilos.css` | `python scripts/revisar_responsivo.py` |
| Cambiar las preguntas del panel de visibilidad | `docs/panel_visibilidad_prompts.csv` | Ninguna pregunta debe nombrar a la marca (hay una prueba) |

## Pruebas

| Comando | Qué cubre |
|---|---|
| `python -m pytest` | Todo Python: datos, reglas, modelo, mensajes, respuestas, ingesta, simulación, visibilidad, aplicación Dash y que los archivos web estén ensamblados |
| `python -m pytest tests/test_ingesta.py` | Un solo archivo |
| `node web/prueba_motor.js` | JavaScript contra Python, lead por lead |
| `python scripts/verificar_web.py [url]` | La página en un Chrome real, local o publicada |
| `python scripts/ensamblar_web.py --revisar` | Que `web/motor.js` y `web/app.js` coincidan con `web/fuente/` |

La prueba completa de Python tarda unos 4 minutos porque entrena el modelo y recorre la aplicación.

## Versiones

Seguimos [versionado semántico](https://semver.org/lang/es/) y [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). La versión está en `pyproject.toml` y en `recontacto.__version__`; cada versión tiene su entrada en `CHANGELOG.md`.
