# `web/` · versión que abre sin instalar nada

Una sola página (`entrega.html`) con la herramienta, el memo, la bitácora, el video y la prueba con dos personas. En GitHub Pages es `index.html`. Calcula todo en el navegador y los datos no salen de él.

| Ruta | Contenido | ¿Se edita a mano? |
|---|---|---|
| `fuente/motor/NN_*.js` | Lógica, una sección por archivo | Sí |
| `fuente/app/NN_*.js` | Interfaz, una sección por archivo | Sí |
| `motor.js`, `app.js` | Resultado de unir las secciones | **No**: `python scripts/ensamblar_web.py` |
| `plantilla.html`, `estilos.css` | Estructura, memo, bitácora y estilos de Clivi | Sí |
| `datos.json`, `modelo.json`, `evidencia.json`, `referencia.json`, `casos_*.json` | Lo que Python calcula para la web | **No**: `python scripts/exportar_web.py` |
| `entrega.html` | Página final | **No**: `python scripts/construir_web.py` |
| `prueba_motor.js` | Compara JavaScript contra Python | Sí |

Flujo completo: `bat\construir_web.bat`.

Límites: el modelo no se reentrena aquí, no lee Parquet, bases de datos ni la nube, y las bajas viven en el navegador (`localStorage`).
