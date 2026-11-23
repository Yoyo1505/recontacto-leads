# `app/` · aplicación Dash

Aplicación con nueve secciones. `dash_app.py` solo ensambla (encabezado, barra lateral con las reglas, menú y rutas); cada sección vive en su archivo.

```
python app/dash_app.py            abre http://127.0.0.1:8050
python app/dash_app.py --puerto 8060
```

(O `bat\iniciar_app.bat`.)

| Archivo | Contenido |
|---|---|
| `dash_app.py` | Ensamblado, controles de reglas y estado compartido |
| `contexto.py` | Datos, modelo y cálculos pesados en caché; se recarga tras actualizar datos |
| `tema.py`, `componentes.py`, `assets/` | Colores, piezas reutilizables y estilos |
| `secciones/resumen.py` | Portada: embudo y no contesta por canal |
| `secciones/lista.py` | Lista del día, mapa de calor, detalle y descarga |
| `secciones/mensajes.py` | Biblioteca de mensajes por situación y variantes |
| `secciones/respuestas.py` | Probar qué entiende la herramienta de una respuesta |
| `secciones/evidencia.py` | Intervalos, calibración, carta p y embudo de asesores |
| `secciones/simulacion.py` | Monte Carlo con sensibilidad a `alpha` |
| `secciones/prueba_ab.py` | Tamaño de muestra, potencia y duración |
| `secciones/datos.py` | Subir archivos, agregar personas, bajas y versiones |
| `secciones/limites.py` | Lo que no se puede afirmar y los supuestos |

Para agregar una sección: un módulo con `ID`, `TITULO`, `RUTA`, `layout(ctx)` y `registrar(app, ctx)`, y una línea en `secciones/__init__.py`.
