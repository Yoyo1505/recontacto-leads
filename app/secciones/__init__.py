"""Registro de secciones de la aplicacion.

Cada seccion es un modulo con la misma interfaz:
    ID, TITULO, RUTA        identifican la seccion y su direccion (por ejemplo /lista)
    layout(ctx)             devuelve los componentes de la pagina
    registrar(app, ctx)     registra sus callbacks (puede no hacer nada)

Para agregar una seccion: crea el modulo, importalo aqui y anadelo a `SECCIONES`.
Para quitar una: borrala de `SECCIONES`. El orden de la lista es el orden del menu.
"""

from . import datos, evidencia, limites, lista, mensajes, prueba_ab, respuestas, resumen, simulacion

SECCIONES = [resumen, lista, mensajes, respuestas, evidencia, simulacion, prueba_ab, datos, limites]
POR_RUTA = {s.RUTA: s for s in SECCIONES}
