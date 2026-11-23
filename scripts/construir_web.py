"""Arma el sitio de la entrega: una pagina por entrega, en web/sitio/.

Paginas
    index.html         solo redirige a herramienta.html (para que la direccion raiz del sitio funcione)
    herramienta.html   entrega 1: la herramienta (lleva datos, modelo y motor)
    memo.html          entrega 2: memo de una pagina
    bitacora.html      entrega 3: bitacora
    video.html         entrega 4: video, demos para simular y prueba con dos personas
    demo.mp4           el video (se copia de docs/demo/demo.mp4)

Cada pagina es un documento completo que se abre con doble clic o se sube a cualquier hosting (GitHub Pages,
Netlify...). Todas comparten encabezado, estilos y pie; solo la herramienta carga el motor y los datos.

Antes hay que exportar datos y modelo: python scripts/exportar_web.py
Despues de armar, comprobar el motor: node web/prueba_motor.js

Donde cambiar cosas
    - Estructura comun (encabezado, pie, menu): web/paginas/base.html.
    - Contenido de cada entrega: web/paginas/<nombre>.html (memo, bitacora, video).
    - Estilos: web/estilos.css. Logica de la herramienta: las secciones de web/fuente/ (se ensamblan solas).
    - Orden y nombres del menu: constante ENTREGAS.
    - Capitulos del video: docs/demo/capitulos.json (los escribe crear_video.py).
"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ensamblar_web  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "web"
SITIO = WEB / "sitio"

ENTREGAS = (
    ("herramienta", "1 · Herramienta", "Entrega 1 · Herramienta de recontacto"),
    ("memo", "2 · Memo", "Entrega 2 · Memo de una página"),
    ("bitacora", "3 · Bitácora", "Entrega 3 · Bitácora"),
    ("video", "4 · Video y prueba", "Entrega 4 · Video, demos y prueba con dos personas"),
)

REDIRECCION = (
    '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta http-equiv="refresh" content="0; url=herramienta.html">\n<link rel="canonical" href="herramienta.html">\n<title>Recontacto de leads</title>\n</head>\n'
    '<body><p><a href="herramienta.html">Ir a la herramienta (entrega 1)</a></p></body>\n</html>\n'
)

CAPITULOS = "Capítulos: 0:00 presentación · 0:05 el problema · 0:15 recorrido · 2:53 lo que sigue."


def capitulos_texto():
    archivo = RAIZ / "docs" / "demo" / "capitulos.json"
    if not archivo.exists():
        return CAPITULOS
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    marcas = " · ".join(f"{c['inicio'] // 60}:{c['inicio'] % 60:02d} {c['titulo']}" for c in datos["capitulos"])
    return f"Duración {datos['duracion'] // 60}:{datos['duracion'] % 60:02d}. Capítulos: {marcas}."


def leer(ruta):
    return (WEB / ruta).read_text(encoding="utf-8")


def compacto(nombre):
    return json.dumps(json.loads(leer(nombre)), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def logo_datos():
    """Logo de Clivi como data URI, reducido para que pese poco."""
    import base64
    import io

    from PIL import Image

    imagen = Image.open(RAIZ / "docs" / "marca" / "logo-clivi.png").convert("RGBA")
    ancho = 240
    imagen = imagen.resize((ancho, round(imagen.height * ancho / imagen.width)), Image.LANCZOS)
    buffer = io.BytesIO()
    imagen.save(buffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def menu(actual):
    enlaces = []
    for clave, texto, _ in ENTREGAS:
        marca = ' aria-current="page"' if clave == actual else ""
        enlaces.append(f'      <a href="{clave}.html"{marca}>{texto}</a>')
    return "\n".join(enlaces)


def scripts_herramienta():
    return "\n".join(
        [
            f'<script type="application/json" id="datos-json">{compacto("datos.json")}</script>',
            f'<script type="application/json" id="modelo-json">{compacto("modelo.json")}</script>',
            f'<script type="application/json" id="evidencia-json">{compacto("evidencia.json")}</script>',
            '<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>',
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>',
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>',
            "<script>\n" + leer("motor.js") + "\n</script>",
            "<script>\n" + leer("app.js") + "\n</script>",
        ]
    )


def contenido(clave):
    if clave == "herramienta":
        return '<section id="vista-herramienta" class="vista"></section>'
    texto = leer(f"paginas/{clave}.html")
    return texto.replace("{{CAPITULOS}}", capitulos_texto())


def main():
    ensamblar_web.main([])
    base = leer("paginas/base.html")
    css = leer("estilos.css")
    logo = logo_datos()
    SITIO.mkdir(exist_ok=True)
    for clave, _, titulo in ENTREGAS:
        pagina = base
        for marcador, valor in {
            "{{TITULO}}": titulo,
            "{{CSS}}": css,
            "{{LOGO}}": logo,
            "{{NAV}}": menu(clave),
            "{{CONTENIDO}}": contenido(clave),
            "{{SCRIPTS}}": scripts_herramienta() if clave == "herramienta" else "",
        }.items():
            pagina = pagina.replace(marcador, valor)
        if re.search(r"\{\{[A-Z_]+\}\}", pagina):
            raise SystemExit(f"Quedaron marcadores sin reemplazar en {clave}.html")
        (SITIO / f"{clave}.html").write_text(pagina, encoding="utf-8")
        print(f"{clave}.html", round((SITIO / f"{clave}.html").stat().st_size / 1024), "KB")
    (SITIO / "index.html").write_text(REDIRECCION, encoding="utf-8")
    video = RAIZ / "docs" / "demo" / "demo.mp4"
    if video.exists():
        shutil.copy2(video, SITIO / "demo.mp4")


if __name__ == "__main__":
    sys.exit(main())
