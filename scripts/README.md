# `scripts/` · tareas de apoyo

| Script | Qué hace | Cuándo |
|---|---|---|
| `exportar_web.py` | Calcula con Python los datos, el modelo y los casos de prueba de la versión web | Tras cambiar datos, modelo o reglas |
| `ensamblar_web.py` | Une `web/fuente/` en `web/motor.js` y `web/app.js` (`--revisar` solo comprueba) | Tras editar la web |
| `construir_web.py` | Ensambla y arma las cinco páginas de `web/sitio/` | Antes de publicar |
| `revisar_responsivo.py` | Comprueba que cada página conserve su formato de 360 a 1440 px (pantalla dividida incluida) | Tras cambiar estilos o contenido |
| `verificar_web.py` | Recorre la herramienta y las demás páginas en un Chrome real; acepta una URL | Antes de publicar |
| `grabar_demo.py` | Regraba el GIF de la aplicación (con la app corriendo) | Si cambian las pantallas |
| `crear_video.py` | Crea el video de 3 minutos con capítulos | Si cambian las pantallas |
| `probar_llm_local.py` | Prueba un modelo local (Ollama) como redactor de mensajes | Para evaluar un modelo |
| `experimento_recomendacion.py` | Experimento de recomendación con un modelo local | Para evaluar contenido |

Los `.bat` de `bat/` llaman a estos scripts con el entorno correcto.
