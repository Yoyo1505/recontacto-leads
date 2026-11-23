# `web/` · versión que abre sin instalar nada

Un sitio de cuatro páginas, una por entrega, en `sitio/`: `herramienta.html` (entrega 1), `memo.html` (2), `bitacora.html` (3) y `video.html` (4: video, demos para simular y prueba con dos personas). `index.html` solo redirige a la herramienta para que la dirección raíz funcione. Solo la herramienta carga el motor y los datos, y calcula todo en el navegador: los datos no salen de él.

| Ruta | Contenido | ¿Se edita a mano? |
|---|---|---|
| `fuente/motor/NN_*.js` | Lógica, una sección por archivo | Sí |
| `fuente/app/NN_*.js` | Interfaz, una sección por archivo | Sí |
| `motor.js`, `app.js` | Resultado de unir las secciones | **No**: `python scripts/ensamblar_web.py` |
| `paginas/base.html` | Encabezado, menú y pie comunes a todas las páginas | Sí |
| `paginas/memo.html`, `bitacora.html`, `video.html` | Contenido de cada entrega | Sí |
| `estilos.css` | Estilos de Clivi y las reglas para pantallas angostas | Sí |
| `datos.json`, `modelo.json`, `evidencia.json`, `referencia.json`, `casos_*.json` | Lo que Python calcula para la web | **No**: `python scripts/exportar_web.py` |
| `sitio/` | Las cuatro páginas, la redirección y `demo.mp4`, listas para publicar | **No**: `python scripts/construir_web.py` |
| `prueba_motor.js` | Compara JavaScript contra Python | Sí |

Flujo completo: `bat\construir_web.bat`.

Límites: el modelo no se reentrena aquí, no lee Parquet, bases de datos ni la nube, y las bajas viven en el navegador (`localStorage`).
