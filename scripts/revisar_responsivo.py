"""Revisa que cada pagina del sitio conserve su formato en pantallas angostas (por ejemplo, pantalla dividida).

Que comprueba, en cada pagina y a cada ancho
    - No hay desplazamiento horizontal de la pagina (nada se sale por la derecha).
    - Ningun elemento visible se sale del ancho de la ventana (se listan los que lo hacen).
    - El encabezado, el menu y el contenido se ven (y la herramienta dibuja su lista).
Con --capturas guarda una imagen por pagina y ancho para revisarlas a ojo.

Anchos: los de una ventana completa, de media pantalla (pantalla dividida en monitores de 1366 a 1920 px) y de telefono.

Uso
    python scripts/revisar_responsivo.py                       revisa web/sitio/
    python scripts/revisar_responsivo.py --capturas carpeta
    python scripts/revisar_responsivo.py https://yoyo1505.github.io/recontacto-leads/

Donde cambiar cosas
    - Anchos y paginas: constantes ANCHOS y PAGINAS.
    - Estilos que se corrigen: web/estilos.css (bloques @media).
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grabar_demo as g  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
ANCHOS = (1440, 1100, 960, 800, 683, 540, 390, 360)
PAGINAS = ("herramienta", "memo", "bitacora", "video")

BUSCAR_DESBORDES = """
(() => {
  const ancho = document.documentElement.clientWidth;
  const malos = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || r.left < -1000) continue;
    const est = getComputedStyle(e);
    if (est.visibility === 'hidden' || est.display === 'none') continue;
    if (r.right > ancho + 1 || r.left < -1) {
      let dentro = false;
      for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
        const o = getComputedStyle(p).overflowX;
        if (o === 'auto' || o === 'scroll' || o === 'hidden') { dentro = true; break; }
      }
      if (!dentro) malos.push((e.tagName + '.' + (e.className || '').toString().split(' ')[0] + '#' + (e.id || '')).slice(0, 60) + ' [' + Math.round(r.left) + '..' + Math.round(r.right) + ']');
    }
  }
  return JSON.stringify({ ancho, scroll: document.documentElement.scrollWidth, malos: malos.slice(0, 6) });
})()
"""


def url_de(base, pagina):
    if "://" in base:
        return base.rstrip("/") + "/" + pagina + ".html"
    return (Path(base) / f"{pagina}.html").resolve().as_uri()


def main(argumentos=None):
    import json

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("base", nargs="?", default=str(RAIZ / "web" / "sitio"))
    parser.add_argument("--capturas", default=None)
    args = parser.parse_args(argumentos)
    carpeta = Path(args.capturas) if args.capturas else None
    if carpeta:
        carpeta.mkdir(parents=True, exist_ok=True)
    fallos = 0
    nav = g.Navegador(puerto=9488, ancho=1440, alto=900)
    try:
        for pagina in PAGINAS:
            for ancho in ANCHOS:
                nav.enviar("Emulation.setDeviceMetricsOverride", width=ancho, height=900, deviceScaleFactor=1, mobile=False)
                nav.ir(url_de(args.base, pagina), 1.2)
                if pagina == "herramienta":
                    g.esperar(nav, "#l-tabla tbody tr")
                    time.sleep(1.0)
                datos = json.loads(nav.js(BUSCAR_DESBORDES))
                horizontal = datos["scroll"] > datos["ancho"] + 1
                visible = nav.js("!!document.querySelector('header.superior nav.piezas a') && document.querySelector('main').getBoundingClientRect().height > 100")
                bien = not horizontal and not datos["malos"] and visible
                fallos += 0 if bien else 1
                estado = "ok " if bien else "MAL"
                detalle = "" if bien else f" scroll={datos['scroll']} > {datos['ancho']} · {'; '.join(datos['malos'])}"
                print(f"  {estado} {pagina:12} {ancho:5}px{detalle}")
                if carpeta:
                    nav.foto().save(carpeta / f"{pagina}_{ancho}.png")
    finally:
        nav.cerrar()
    print("RESULTADO:", "todo bien" if not fallos else f"{fallos} combinaciones con problemas")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
