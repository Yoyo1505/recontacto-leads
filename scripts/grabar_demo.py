"""Graba el GIF de la presentacion manejando Chrome por su protocolo de depuracion (CDP).

Que hace
    Abre un Chrome temporal (perfil aparte, sin tocar el tuyo), recorre la aplicacion con clics y
    cambios reales de controles, toma un fotograma por paso y arma docs/demo/demo.gif con un
    subtitulo en cada uno.

Requisitos
    - Chrome instalado (o la variable de entorno CHROME_EXE con su ruta).
    - La aplicacion corriendo: python app/dash_app.py   (http://127.0.0.1:8050)
    - pillow y websocket-client.

Uso
    python scripts/grabar_demo.py
    python scripts/grabar_demo.py --url http://127.0.0.1:8060 --ancho-gif 900

Donde cambiar cosas
    - Pasos de la presentacion y sus subtitulos: funcion `recorrer`.
    - Tiempo de cada fotograma: tercer argumento de `captura`, en milisegundos.
    - Tamano y colores del GIF: constantes y funcion `componer`.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from io import BytesIO
from pathlib import Path

import websocket
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "docs" / "demo"
CHROME = os.environ.get("CHROME_EXE", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
FUENTE = r"C:\Windows\Fonts\segoeuib.ttf"
COLOR_BARRA = (0, 45, 66)
COLOR_ACENTO = (0, 169, 157)
CODIGOS_TECLA = {"ArrowLeft": 37, "ArrowRight": 39, "Home": 36, "End": 35}


class Navegador:
    def __init__(self, puerto=9333, ancho=1280, alto=760):
        self.carpeta = tempfile.mkdtemp(prefix="clivi_demo_")
        self.proceso = subprocess.Popen(
            [
                CHROME,
                "--headless=new",
                f"--remote-debugging-port={puerto}",
                f"--user-data-dir={self.carpeta}",
                "--hide-scrollbars",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        destino = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json/list", timeout=2) as r:
                    paginas = [p for p in json.loads(r.read()) if p.get("type") == "page"]
                if paginas:
                    destino = paginas[0]["webSocketDebuggerUrl"]
                    break
            except OSError:
                pass
            time.sleep(0.5)
        if not destino:
            self.cerrar()
            raise RuntimeError("No se pudo conectar con Chrome")
        self.ws = websocket.create_connection(destino, timeout=60)
        self._id = 0
        self.enviar("Page.enable")
        self.enviar("Emulation.setDeviceMetricsOverride", width=ancho, height=alto, deviceScaleFactor=1, mobile=False)

    def enviar(self, metodo, **parametros):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": metodo, "params": parametros}))
        while True:
            mensaje = json.loads(self.ws.recv())
            if mensaje.get("id") == self._id:
                if "error" in mensaje:
                    raise RuntimeError(f"{metodo}: {mensaje['error']}")
                return mensaje.get("result", {})

    def js(self, expresion):
        resultado = self.enviar("Runtime.evaluate", expression=expresion, returnByValue=True, awaitPromise=True)
        return resultado.get("result", {}).get("value")

    def ir(self, url, espera=4.0):
        self.enviar("Page.navigate", url=url)
        time.sleep(espera)

    def foto(self):
        datos = self.enviar("Page.captureScreenshot", format="png")["data"]
        return Image.open(BytesIO(base64.b64decode(datos))).convert("RGB")

    def tecla(self, clave):
        codigo = CODIGOS_TECLA[clave]
        for tipo in ("rawKeyDown", "keyUp"):
            self.enviar("Input.dispatchKeyEvent", type=tipo, key=clave, code=clave, windowsVirtualKeyCode=codigo)

    def cerrar(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.proceso.terminate()
        time.sleep(1)
        shutil.rmtree(self.carpeta, ignore_errors=True)


def existe(nav, selector):
    return bool(nav.js(f"!!document.querySelector({json.dumps(selector)})"))


def esperar(nav, selector, intentos=80):
    for _ in range(intentos):
        if existe(nav, selector):
            return
        time.sleep(0.5)
    raise RuntimeError(f"No apareció {selector}")


def esperar_valor(nav, selector, intentos=120):
    esperar(nav, selector)
    for _ in range(intentos):
        texto = nav.js(f"document.querySelector({json.dumps(selector)}).textContent")
        if texto and texto.strip() not in ("-", ""):
            return texto
        time.sleep(0.5)
    raise RuntimeError(f"{selector} nunca tuvo valor")


def clic(nav, selector):
    esperar(nav, selector)
    nav.js(f"document.querySelector({json.dumps(selector)}).click()")


def menu(nav, texto):
    nav.js(
        "[...document.querySelectorAll('.menu a')].find(a => a.textContent.trim() === "
        + json.dumps(texto)
        + ").click()"
    )
    time.sleep(2.5)


def desplazar(nav, selector, margen=90):
    esperar(nav, selector)
    nav.js(
        f"window.scrollTo(0, document.querySelector({json.dumps(selector)}).getBoundingClientRect().top + window.scrollY - {margen})"
    )
    time.sleep(0.8)


def subir_archivo(nav, ruta):
    documento = nav.enviar("DOM.getDocument")["root"]["nodeId"]
    nodo = nav.enviar("DOM.querySelector", nodeId=documento, selector="#datos-subir input[type=file]")["nodeId"]
    nav.enviar("DOM.setFileInputFiles", files=[ruta], nodeId=nodo)


def arriba(nav):
    nav.js("window.scrollTo(0, 0)")
    time.sleep(0.6)


def mover_control(nav, selector, tecla, veces=1, pausa=3.0):
    esperar(nav, selector)
    nav.js(f"document.querySelector({json.dumps(selector)} + ' [role=\"slider\"]').focus()")
    for _ in range(veces):
        nav.tecla(tecla)
        time.sleep(0.15)
    time.sleep(pausa)
    nav.js("document.activeElement && document.activeElement.blur()")
    time.sleep(0.3)


def componer(imagen, subtitulo, ancho):
    alto_barra = 56
    base = imagen.copy()
    dibujo = ImageDraw.Draw(base)
    alto = base.height
    dibujo.rectangle([0, alto - alto_barra, base.width, alto], fill=COLOR_BARRA)
    dibujo.rectangle([0, alto - alto_barra, 8, alto], fill=COLOR_ACENTO)
    fuente = ImageFont.truetype(FUENTE, 24) if Path(FUENTE).exists() else ImageFont.load_default()
    dibujo.text((28, alto - alto_barra + 14), subtitulo, font=fuente, fill=(255, 255, 255))
    proporcion = ancho / base.width
    return base.resize((ancho, round(base.height * proporcion)), Image.LANCZOS)


def recorrer(nav, url):
    fotogramas = []

    def captura(subtitulo, milisegundos):
        fotogramas.append((nav.foto(), subtitulo, milisegundos))

    nav.ir(url, 5)
    esperar_valor(nav, "#kpi-resumen-leads")
    time.sleep(1.5)
    captura("Resumen: cuatro de cada diez personas no contestan", 3500)

    menu(nav, "Lista del día")
    esperar_valor(nav, "#kpi-lista-total")
    captura("Lista del día: quién, cuándo y con qué mensaje", 2800)

    desplazar(nav, "#tabla-lista", 80)
    captura("Ordenable y filtrable; nadie se descarta por probabilidad baja", 2800)
    for _ in range(5):
        clic(nav, "#tabla-lista .next-page")
        time.sleep(0.4)
    clic(nav, "#tabla-lista input[type=radio]")
    time.sleep(1)
    desplazar(nav, "#detalle-lead", 360)
    captura("Cada recomendación explica su motivo y trae su mensaje", 3800)

    arriba(nav)
    mover_control(nav, "#ctl-intentos", "ArrowLeft", 1, 3.0)
    captura("Cambia una regla (2 intentos) y la lista se recalcula", 3000)
    mover_control(nav, "#ctl-intentos", "ArrowRight", 1, 2.0)

    menu(nav, "Evidencia")
    esperar(nav, "#grafica-tasas")
    time.sleep(2.5)
    captura("Evidencia: cuánta confianza merece cada hallazgo", 2800)
    desplazar(nav, "#grafica-confusion", 140)
    captura("La hora y la espera van juntas: no se pueden separar", 3500)
    desplazar(nav, "#grafica-carta-p", 140)
    captura("Control estadístico: ¿algo se sale del azar?", 3000)

    menu(nav, "Simulación")
    esperar_valor(nav, "#kpi-sim-media")
    time.sleep(1.5)
    captura("Simulación (alpha 0.5): la mejora es incierta", 3500)
    mover_control(nav, "#sim-alpha", "Home", 1, 3.0)
    captura("Si el horario no importara (alpha 0): sin mejora", 3000)
    mover_control(nav, "#sim-alpha", "End", 1, 3.0)
    captura("Si todo fuera causal (alpha 1): mejora, pero con intervalo amplio", 3500)

    menu(nav, "Prueba A/B")
    esperar_valor(nav, "#kpi-ab-n")
    time.sleep(1.2)
    captura("Prueba A/B: detectar +3 puntos pide miles de personas", 3500)
    mover_control(nav, "#ab-efecto", "End", 1, 2.0)
    captura("Un efecto de 12 puntos se comprobaría en pocas semanas", 3000)

    menu(nav, "Datos")
    esperar_valor(nav, "#kpi-datos-leads")
    captura("Datos: sube un archivo y la herramienta explica qué haría", 3000)
    subir_archivo(nav, str(RAIZ / "data" / "ejemplos" / "dos_personas_nuevas.csv"))
    esperar(nav, "#datos-informe h4")
    time.sleep(1.5)
    desplazar(nav, "#datos-informe", 110)
    captura("Dos personas nuevas: una se agenda hoy, otra en su mejor horario", 4800)
    fotogramas[-1][0].save(RAIZ / "docs" / "capturas" / "datos.png")

    menu(nav, "Límites")
    time.sleep(1.5)
    captura("Límites: lo que los datos no permiten afirmar", 3000)
    return fotogramas


def armar_gif(fotogramas, ruta, ancho, colores):
    cuadros, duraciones = [], []
    for imagen, subtitulo, ms in fotogramas:
        chico = componer(imagen, subtitulo, ancho)
        cuadros.append(chico.quantize(colors=colores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        duraciones.append(ms)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cuadros[0].save(ruta, save_all=True, append_images=cuadros[1:], duration=duraciones, loop=0, optimize=True, disposal=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--ancho-gif", type=int, default=1000)
    parser.add_argument("--colores", type=int, default=128)
    parser.add_argument("--salida", default=str(SALIDA / "demo.gif"))
    args = parser.parse_args()

    nav = Navegador()
    try:
        fotogramas = recorrer(nav, args.url)
    finally:
        nav.cerrar()
    ruta = Path(args.salida)
    armar_gif(fotogramas, ruta, args.ancho_gif, args.colores)
    print(f"{len(fotogramas)} fotogramas -> {ruta} ({ruta.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
