"""Crea el video MP4 de la presentacion (unos tres minutos).

Que incluye
    1. Tarjeta de titulo y tarjeta del problema.
    2. Recorrido por la aplicacion en Dash (un fotograma por paso, con subtitulo) y, en medio,
       dos conversaciones de ejemplo (ILUSTRATIVAS: las respuestas son inventadas y el video lo dice).
    3. Escenas de la pagina web de entrega, que abre sin instalar nada.
    4. Tarjetas con lo que se encontro, lo que no funciona todavia y lo que sigue.
    Todo se une con fundidos y se graba en tiempo real con Chrome (MediaRecorder, H.264):
    no hace falta ffmpeg ni instalar nada.

Salidas
    docs/demo/demo.mp4          el video
    docs/demo/capitulos.json    en que segundo empieza cada capitulo (lo usa construir_web.py)

Requisitos
    - Chrome instalado.
    - La aplicacion corriendo: python app/dash_app.py   (http://127.0.0.1:8050)
    - La pagina web armada:   python scripts/construir_web.py   (web/entrega.html)
    - pillow y websocket-client.

Uso
    python scripts/crear_video.py
    python scripts/crear_video.py --bitrate 1500000 --salida C:\\ruta\\demo.mp4

Donde cambiar cosas
    - Textos de las tarjetas y conversaciones: constantes CONVERSACION_*, TARJETA_*.
    - Duracion de cada pantalla: segundos en `armar_piezas`.
    - Peso del archivo: --bitrate (menos bits, archivo mas ligero).
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grabar_demo as demo  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
ANCHO, ALTO = 1280, 760
FUENTE = r"C:\Windows\Fonts\segoeui.ttf"
FUENTE_NEGRITA = r"C:\Windows\Fonts\segoeuib.ttf"
AZUL_OSCURO = (0, 45, 66)
AZUL = (0, 84, 124)
TURQUESA = (0, 169, 157)
AMBAR = (178, 106, 0)
TINTA = (11, 31, 44)
FONDO = (233, 238, 242)
FACTOR_APP = 1.35

MENSAJE_RETOMA = (
    "Hola, te escribe Asesor B de Clivi. Intenté comunicarme contigo por tu solicitud de información "
    "y no logramos hablar. Cuando tengas un momento, dime si prefieres que te llame o seguir por mensaje. "
    "Si prefieres que no te escribamos, responde NO."
)
CONVERSACION_RETOMA = {
    "titulo": "Una conversación que se recupera",
    "mensajes": [
        ("asesor", MENSAJE_RETOMA),
        ("persona", "Hola, mejor por mensaje. Hoy en la tarde sí puedo."),
        ("asesor", "Perfecto, te escribo a las 4:00 pm con la información. Gracias por contestar."),
    ],
    "lado": [
        "La herramienta eligió a esta persona y el horario.",
        "El mensaje es el de la plantilla de segundo intento: una pregunta fácil, con el control en manos de la persona.",
        "Al contestar, el asesor actualiza su estado a «en seguimiento» y sale de la lista de recontacto.",
    ],
    "subtitulo": "Ejemplo: la persona contesta y la conversación sigue",
}
CONVERSACION_BAJA = {
    "titulo": "Cuando alguien pide no recibir más mensajes",
    "mensajes": [
        ("asesor", MENSAJE_RETOMA),
        ("persona", "NO"),
        ("asesor", "Entendido, no te volveremos a escribir. Gracias por tu tiempo."),
    ],
    "lado": [
        "Todo mensaje trae la forma de pedir que no se le escriba más.",
        "El asesor registra el teléfono en la lista de bajas (hoy a mano) y ya no aparece en ninguna lista, aunque llegue en archivos futuros.",
        "Nadie nos debe una respuesta: respetar la baja también es recuperar la confianza.",
    ],
    "subtitulo": "Ejemplo: se respeta la baja para siempre",
}
AVISO_EJEMPLO = "EJEMPLO ILUSTRATIVO · las respuestas de la persona son inventadas y la lectura automática de respuestas todavía no existe"
TARJETA_TITULO = ("Recontacto de leads", "Misión C: que más personas contesten", "A quién volver a buscar, cuándo y con qué mensaje.\nCuidando el trato: nadie nos debe una respuesta.", "Datos ficticios · demostración")
TARJETA_PROBLEMA = (
    "El problema",
    [
        "Cuatro de cada diez personas que pidieron información no contestan cuando un asesor las busca.",
        "La herramienta dice a quién volver a buscar, cuándo y con qué mensaje.",
        "Cuida el trato: máximo 3 intentos, un cierre amable y respeto absoluto a quien pide no recibir mensajes.",
        "Abre sin instalar nada, en el navegador.",
    ],
)
TARJETA_HALLAZGOS = (
    "Lo que encontré",
    [
        "El 40.3% de los 1,694 leads contactados no contestó",
        "El canal marca la diferencia: 24% de los referidos contra 49% de TikTok",
        "Contactar en 30 minutos: 29% sin respuesta. Tras 12 a 24 horas: 47%",
        "El modelo tiene señal modesta: AUC 0.60 (intervalo 0.55 a 0.65)",
        "Un día de lista: +5.7 personas, intervalo de −20 a +31. No se distingue del azar",
        "Comprobar +3 puntos pide unas 4,100 personas por grupo, unos 200 días",
    ],
)
TARJETA_LIMITES = (
    "Lo que no funciona todavía",
    [
        "No envía mensajes ni lee respuestas: la baja se registra a mano",
        "Los mensajes son tres plantillas, no probadas con respuestas reales",
        "Horario y rapidez del contacto no se pueden separar con estos datos",
        "El modelo no se reentrena en el navegador",
        "No probé nube, PostgreSQL, MySQL ni el modelo de lenguaje con servicios reales",
        "La prueba con dos personas está pendiente",
    ],
)
TARJETA_CIERRE = (
    "Lo que sigue",
    [
        "Probar con dos personas y registrar lo que cambie",
        "Mensajes por situación, con variantes para comparar",
        "Que las respuestas (sí, no, a tal hora) actualicen el estado solas",
        "Prueba A/B para medir cuánto recupera cada mensaje",
    ],
)

RECORDER_HTML = """<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#000"><canvas id="c" width="%(w)d" height="%(h)d"></canvas>
<script>
const W=%(w)d,H=%(h)d,FPS=30,FADE=0.6;
(async()=>{
  const plan=await (await fetch('plan.json')).json();
  const imgs=[];
  for(const p of plan){const b=await (await fetch(p.archivo)).blob(); imgs.push(await createImageBitmap(b));}
  const c=document.getElementById('c'),x=c.getContext('2d');
  const tipos=['video/mp4;codecs=avc1.42E01E','video/mp4','video/webm;codecs=vp9','video/webm'];
  const tipo=tipos.find(t=>MediaRecorder.isTypeSupported(t));
  const rec=new MediaRecorder(c.captureStream(FPS),{mimeType:tipo,videoBitsPerSecond:%(bps)d});
  const partes=[]; rec.ondataavailable=e=>{if(e.data.size)partes.push(e.data)};
  const fin=new Promise(r=>rec.onstop=r);
  let acumulado=0; const inicios=plan.map(p=>{const s=acumulado;acumulado+=p.segundos;return s}); const total=acumulado;
  x.drawImage(imgs[0],0,0,W,H);
  rec.start(500);
  const t0=performance.now();
  await new Promise(res=>{const id=setInterval(()=>{
    const t=(performance.now()-t0)/1000;
    if(t>=total){clearInterval(id);res();return}
    let i=0; for(let k=0;k<inicios.length;k++){ if(t>=inicios[k]) i=k; }
    x.globalAlpha=1; x.drawImage(imgs[i],0,0,W,H);
    const resta=inicios[i]+plan[i].segundos-t;
    if(i<plan.length-1&&resta<FADE){x.globalAlpha=1-resta/FADE; x.drawImage(imgs[i+1],0,0,W,H);}
  },1000/FPS)});
  await new Promise(r=>setTimeout(r,400));
  rec.stop(); await fin;
  const blob=new Blob(partes,{type:tipo});
  await fetch('/guardar?ext='+(tipo.includes('mp4')?'mp4':'webm'),{method:'POST',body:blob});
  document.title='listo';
})();
</script>
"""


def fuente(tamano, negrita=False):
    ruta = FUENTE_NEGRITA if negrita else FUENTE
    return ImageFont.truetype(ruta, tamano) if Path(ruta).exists() else ImageFont.load_default()


def envolver(dibujo, texto, tipo, ancho):
    lineas = []
    for parrafo in texto.split("\n"):
        actual = ""
        for palabra in parrafo.split():
            prueba = f"{actual} {palabra}".strip()
            if dibujo.textlength(prueba, font=tipo) <= ancho:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def barra_subtitulo(imagen, texto):
    dibujo = ImageDraw.Draw(imagen)
    alto_barra = 56
    dibujo.rectangle([0, ALTO - alto_barra, ANCHO, ALTO], fill=AZUL_OSCURO)
    dibujo.rectangle([0, ALTO - alto_barra, 8, ALTO], fill=TURQUESA)
    dibujo.text((28, ALTO - alto_barra + 11), texto, font=fuente(24, True), fill=(255, 255, 255))


def tarjeta_titulo():
    titulo, sub, texto, pie = TARJETA_TITULO
    imagen = Image.new("RGB", (ANCHO, ALTO), AZUL_OSCURO)
    d = ImageDraw.Draw(imagen)
    d.rectangle([90, 250, 98, 440], fill=TURQUESA)
    d.text((130, 236), titulo, font=fuente(72, True), fill=(255, 255, 255))
    d.text((132, 332), sub, font=fuente(34), fill=(160, 214, 226))
    y = 400
    for linea in texto.split("\n"):
        d.text((132, y), linea, font=fuente(26), fill=(222, 232, 238))
        y += 38
    d.text((132, ALTO - 90), pie, font=fuente(20), fill=(130, 165, 180))
    return imagen


def tarjeta_lista(datos, tamano=30):
    titulo, puntos = datos
    imagen = Image.new("RGB", (ANCHO, ALTO), AZUL_OSCURO)
    d = ImageDraw.Draw(imagen)
    d.text((110, 90), titulo, font=fuente(56, True), fill=(255, 255, 255))
    y = 210
    for punto in puntos:
        d.ellipse([112, y + 12, 128, y + 28], fill=TURQUESA)
        for linea in envolver(d, punto, fuente(tamano), ANCHO - 330):
            d.text((150, y), linea, font=fuente(tamano), fill=(222, 232, 238))
            y += tamano + 12
        y += 14
    return imagen


def burbuja(dibujo, x, y, ancho_max, texto, lado):
    tipo = fuente(21)
    lineas = envolver(dibujo, texto, tipo, ancho_max - 36)
    ancho = max(dibujo.textlength(linea, font=tipo) for linea in lineas) + 36
    alto = len(lineas) * 30 + 24
    izquierda = x if lado == "asesor" else x + ancho_max - ancho
    color = (240, 242, 245) if lado == "asesor" else (205, 232, 228)
    dibujo.rounded_rectangle([izquierda, y, izquierda + ancho, y + alto], radius=16, fill=color)
    for i, linea in enumerate(lineas):
        dibujo.text((izquierda + 18, y + 12 + i * 30), linea, font=tipo, fill=TINTA)
    return y + alto + 16


def tarjeta_conversacion(datos):
    imagen = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(imagen)
    d.rectangle([0, 0, ANCHO, 50], fill=AMBAR)
    d.text((24, 11), AVISO_EJEMPLO, font=fuente(19, True), fill=(255, 255, 255))
    d.rounded_rectangle([50, 80, 690, 690], radius=22, fill=(255, 255, 255))
    d.rounded_rectangle([50, 80, 690, 150], radius=22, fill=AZUL)
    d.rectangle([50, 120, 690, 150], fill=AZUL)
    d.text((80, 94), "Asesor B · Clivi", font=fuente(26, True), fill=(255, 255, 255))
    d.text((80, 124), "Conversación de ejemplo", font=fuente(15), fill=(200, 225, 235))
    y = 175
    for lado, texto in datos["mensajes"]:
        y = burbuja(d, 78, y, 580, texto, lado)
    y = 100
    for linea in envolver(d, datos["titulo"], fuente(30, True), 480):
        d.text((730, y), linea, font=fuente(30, True), fill=TINTA)
        y += 40
    y += 30
    for punto in datos["lado"]:
        d.ellipse([732, y + 9, 744, y + 21], fill=TURQUESA)
        for linea in envolver(d, punto, fuente(23), 470):
            d.text((760, y), linea, font=fuente(23), fill=TINTA)
            y += 33
        y += 20
    barra_subtitulo(imagen, datos["subtitulo"])
    return imagen


def con_subtitulo(imagen, texto):
    marco = imagen.copy().resize((ANCHO, ALTO), Image.LANCZOS)
    barra_subtitulo(marco, texto)
    return marco


def capturar_web(url):
    """Escenas de la pagina de entrega: abre sin instalar nada."""
    nav = demo.Navegador(puerto=9477, ancho=ANCHO, alto=ALTO)
    escenas = []
    try:
        nav.ir(url, 1)
        demo.esperar(nav, "#l-tabla tbody tr")
        time.sleep(2.0)
        escenas.append((nav.foto(), "La página abre en el navegador, sin instalar nada", 6))
        nav.js("document.querySelector('#l-tabla tr.fila').click()")
        time.sleep(0.6)
        nav.js("document.querySelector('#l-detalle').scrollIntoView({block: 'center'})")
        time.sleep(0.8)
        escenas.append((nav.foto(), "Cada recomendación trae su motivo y su mensaje validado", 6))
        nav.js("window.scrollTo(0, 0); document.querySelector('[data-sub=\"simulacion\"]').click()")
        demo.esperar(nav, "#s-kpis .kpi")
        time.sleep(2.0)
        escenas.append((nav.foto(), "Simulación con incertidumbre, en el navegador", 6))
        nav.js("document.querySelector('[data-sub=\"datos\"]').click()")
        time.sleep(0.6)
        nav.js("document.querySelector('#d-ejemplo').click()")
        time.sleep(1.5)
        nav.js("document.querySelector('#d-informe').scrollIntoView({block: 'center'})")
        time.sleep(0.8)
        escenas.append((nav.foto(), "Sube un archivo o agrega personas: informe antes de guardar", 7))
        nav.js("location.hash = '#memo'")
        time.sleep(0.8)
        nav.js("window.scrollTo(0, 0)")
        time.sleep(0.4)
        escenas.append((nav.foto(), "En la misma página: memo, bitácora, video y prueba con dos personas", 6))
    finally:
        nav.cerrar()
    return escenas


def armar_piezas(fotogramas, escenas_web):
    """Devuelve una lista de (imagen, segundos, capitulo o None)."""
    piezas = [(tarjeta_titulo(), 5, "Presentación"), (tarjeta_lista(TARJETA_PROBLEMA), 10, "El problema")]
    primero = True
    for imagen, subtitulo, ms in fotogramas:
        capitulo = None
        if primero:
            capitulo, primero = "Recorrido de la herramienta", False
        elif subtitulo.startswith("Evidencia"):
            capitulo = "Evidencia"
        elif subtitulo.startswith("Simulación"):
            capitulo = "Simulación"
        elif subtitulo.startswith("Prueba A/B"):
            capitulo = "Prueba A/B"
        elif subtitulo.startswith("Datos:"):
            capitulo = "Datos nuevos"
        piezas.append((con_subtitulo(imagen, subtitulo), ms / 1000 * FACTOR_APP, capitulo))
        if "trae su mensaje" in subtitulo:
            piezas.append((tarjeta_conversacion(CONVERSACION_RETOMA), 12, "Conversaciones de ejemplo"))
            piezas.append((tarjeta_conversacion(CONVERSACION_BAJA), 11, None))
    for i, (imagen, subtitulo, segundos) in enumerate(escenas_web):
        piezas.append((con_subtitulo(imagen, subtitulo), segundos, "Versión web, sin instalar" if i == 0 else None))
    piezas.append((tarjeta_lista(TARJETA_HALLAZGOS, 28), 16, "Lo que encontré"))
    piezas.append((tarjeta_lista(TARJETA_LIMITES, 28), 14, "Lo que no funciona todavía"))
    piezas.append((tarjeta_lista(TARJETA_CIERRE), 9, "Lo que sigue"))
    return piezas


def capitulos(piezas):
    salida, t = [], 0.0
    for _, segundos, capitulo in piezas:
        if capitulo:
            salida.append({"inicio": round(t), "titulo": capitulo})
        t += segundos
    return salida, t


def marca(segundos):
    return f"{int(segundos // 60)}:{int(segundos % 60):02d}"


class Servidor(ThreadingHTTPServer):
    pass


def iniciar_servidor(carpeta, destino):
    recibido = threading.Event()

    class Manejador(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(carpeta), **kwargs)

        def log_message(self, *args):
            return

        def do_POST(self):
            longitud = int(self.headers.get("Content-Length", 0))
            datos = self.rfile.read(longitud)
            extension = "mp4" if "ext=mp4" in self.path else "webm"
            ruta = destino.with_suffix("." + extension)
            ruta.write_bytes(datos)
            self.server.guardado = ruta
            self.send_response(200)
            self.end_headers()
            recibido.set()

    servidor = Servidor(("127.0.0.1", 0), Manejador)
    servidor.guardado = None
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor, recibido


def grabar(piezas, destino, bitrate):
    carpeta = Path(tempfile.mkdtemp(prefix="clivi_video_"))
    perfil = Path(tempfile.mkdtemp(prefix="clivi_perfil_"))
    try:
        plan = []
        for i, (imagen, segundos, _) in enumerate(piezas):
            nombre = f"f{i:02d}.png"
            imagen.save(carpeta / nombre)
            plan.append({"archivo": nombre, "segundos": segundos})
        (carpeta / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (carpeta / "grabador.html").write_text(RECORDER_HTML % {"w": ANCHO, "h": ALTO, "bps": bitrate}, encoding="utf-8")
        servidor, recibido = iniciar_servidor(carpeta, destino)
        total = sum(p["segundos"] for p in plan)
        proceso = subprocess.Popen(
            [
                demo.CHROME,
                "--headless=new",
                f"--user-data-dir={perfil}",
                "--autoplay-policy=no-user-gesture-required",
                "--no-first-run",
                "--disable-gpu",
                f"http://127.0.0.1:{servidor.server_port}/grabador.html",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Grabando {total:.0f} s en tiempo real...")
        if not recibido.wait(timeout=total + 180):
            raise RuntimeError("Chrome no entregó el video a tiempo")
        proceso.terminate()
        time.sleep(1)
        servidor.shutdown()
        return servidor.guardado
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
        shutil.rmtree(perfil, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--web", default=str(RAIZ / "web" / "entrega.html"))
    parser.add_argument("--salida", default=str(RAIZ / "docs" / "demo" / "demo.mp4"))
    parser.add_argument("--bitrate", type=int, default=1500000)
    args = parser.parse_args()

    nav = demo.Navegador()
    try:
        fotogramas = demo.recorrer(nav, args.url)
    finally:
        nav.cerrar()
    escenas_web = capturar_web(Path(args.web).resolve().as_uri())
    piezas = armar_piezas(fotogramas, escenas_web)
    marcas, total = capitulos(piezas)
    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    (destino.parent / "capitulos.json").write_text(json.dumps({"duracion": round(total), "capitulos": marcas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Capítulos:", " · ".join(f"{marca(m['inicio'])} {m['titulo']}" for m in marcas))
    ruta = grabar(piezas, destino, args.bitrate)
    print(f"Video: {ruta} ({ruta.stat().st_size / 1e6:.1f} MB, {marca(total)})")


if __name__ == "__main__":
    sys.exit(main())
