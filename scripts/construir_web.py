"""Arma la pagina de entrega a partir de las piezas de web/.

Genera web/entrega.html, un documento completo que se abre con doble clic o se sube a cualquier hosting
(GitHub Pages, Netlify...). El video demo.mp4 va en la misma carpeta.

Antes hay que exportar datos y modelo: python scripts/exportar_web.py
Despues de armar, comprobar el motor: node web/prueba_motor.js

Donde cambiar cosas
    - Texto del memo, la bitacora y la prueba con dos personas: web/plantilla.html.
    - Estilos: web/estilos.css. Logica de la herramienta: las secciones de web/fuente/ (motor y app); este script las ensambla.
    - Capitulos del video: constante CAPITULOS.
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

CAPITULOS = (
    "Capítulos: 0:00 presentación · 0:05 resumen y lista del día · 0:40 ejemplos de conversación · "
    "1:00 evidencia y simulación · 1:55 prueba A/B · 2:15 datos nuevos y bajas · 2:50 lo que sigue."
)


def capitulos_texto():
    archivo = RAIZ / "docs" / "demo" / "capitulos.json"
    if not archivo.exists():
        return CAPITULOS
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    marcas = " · ".join(f"{c['inicio'] // 60}:{c['inicio'] % 60:02d} {c['titulo']}" for c in datos["capitulos"])
    return f"Duración {datos['duracion'] // 60}:{datos['duracion'] % 60:02d}. Capítulos: {marcas}."


def leer(nombre):
    return (WEB / nombre).read_text(encoding="utf-8")


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


def main():
    ensamblar_web.main([])
    plantilla = leer("plantilla.html")
    pieza = {
        "{{CSS}}": leer("estilos.css"),
        "{{LOGO}}": logo_datos(),
        "{{DATOS_JSON}}": compacto("datos.json"),
        "{{MODELO_JSON}}": compacto("modelo.json"),
        "{{EVID_JSON}}": compacto("evidencia.json"),
        "{{MOTOR_JS}}": leer("motor.js"),
        "{{APP_JS}}": leer("app.js"),
        "{{CAPITULOS}}": capitulos_texto(),
    }
    pagina = plantilla
    for clave, valor in pieza.items():
        pagina = pagina.replace(clave, valor)
    if re.search(r"\{\{[A-Z_]+\}\}", pagina):
        raise SystemExit("Quedaron marcadores sin reemplazar")
    (WEB / "entrega.html").write_text(pagina, encoding="utf-8")
    video = RAIZ / "docs" / "demo" / "demo.mp4"
    if video.exists():
        shutil.copy2(video, WEB / "demo.mp4")
    print("entrega.html", round((WEB / "entrega.html").stat().st_size / 1024), "KB")


if __name__ == "__main__":
    sys.exit(main())
