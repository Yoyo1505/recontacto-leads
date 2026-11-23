"""Prueba el sitio de la entrega en un Chrome real: la herramienta (carga, pestanas, reglas, datos nuevos, baja, errores) y las otras cuatro paginas.

Uso:  python scripts/verificar_web.py [ruta o URL de herramienta.html] [--capturas carpeta]
Requiere Chrome, websocket-client y pillow. Sale con codigo 1 si algo falla.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grabar_demo as g  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
CAPTURA_ERRORES = """
window.__errs = [];
window.addEventListener('error', e => window.__errs.push('error: ' + e.message));
window.addEventListener('unhandledrejection', e => window.__errs.push('promesa: ' + (e.reason && e.reason.message || e.reason)));
const ce = console.error; console.error = (...a) => { window.__errs.push('console: ' + a.join(' ')); ce.apply(console, a); };
"""

fallos = []


def comprobar(condicion, mensaje):
    print(("  ok  " if condicion else "  FALLA ") + mensaje)
    if not condicion:
        fallos.append(mensaje)


def esperar_js(nav, expresion, segundos=40):
    for _ in range(int(segundos * 4)):
        if nav.js(expresion):
            return True
        time.sleep(0.25)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destino", nargs="?", default=str(RAIZ / "web" / "sitio" / "herramienta.html"))
    parser.add_argument("--capturas", default=None)
    args = parser.parse_args()
    url = args.destino if "://" in args.destino else Path(args.destino).resolve().as_uri()
    carpeta = Path(args.capturas) if args.capturas else None
    if carpeta:
        carpeta.mkdir(parents=True, exist_ok=True)

    nav = g.Navegador(puerto=9466, ancho=1366, alto=900)
    try:
        nav.enviar("Page.addScriptToEvaluateOnNewDocument", source=CAPTURA_ERRORES)
        nav.ir(url, 1)
        comprobar(esperar_js(nav, "!!window.Plotly && !!window.Papa && !!window.XLSX"), "librerías externas cargadas (Plotly, PapaParse, SheetJS)")
        comprobar(esperar_js(nav, "document.querySelectorAll('#l-tabla tbody tr').length > 0"), "la lista del día se dibuja")
        kpis = nav.js("[...document.querySelectorAll('#l-kpis .v')].map(e => e.textContent).join('|')")
        print("  KPIs:", kpis)
        comprobar(kpis.split("|")[0] == "346", "346 personas por recontactar (igual que Python)")
        comprobar(nav.js("document.querySelectorAll('#l-tabla tbody tr').length") == 12, "12 filas por página")
        comprobar(esperar_js(nav, "document.querySelectorAll('#l-mapa .main-svg').length > 0"), "el mapa de calor se dibuja")
        if carpeta:
            nav.foto().save(carpeta / "01_lista.png")

        nav.js("document.querySelector('#l-tabla tr.fila').click()")
        time.sleep(0.4)
        comprobar("responde NO" in (nav.js("document.querySelector('#l-msg') && document.querySelector('#l-msg').textContent") or ""), "el detalle muestra el mensaje con opción de baja")

        nav.js("document.querySelector('[data-sub=\"mensajes\"]').click()")
        time.sleep(0.8)
        filas_msg = nav.js("document.querySelectorAll('#sub-mensajes tbody tr').length")
        comprobar(filas_msg == 8, f"la biblioteca muestra 8 mensajes (3 + 3 + 2 variantes): {filas_msg}")
        comprobar(nav.js("[...document.querySelectorAll('#sub-mensajes tbody .insignia')].every(e => e.textContent === 'Válido')"), "todas las plantillas pasan el validador")
        nav.js("document.querySelector('#m-comparar').click()")
        time.sleep(0.6)
        solo_a = nav.js("[...new Set(window.__recontacto.E.lista.filas.filter(f => f.variante).map(f => f.variante))].join('')")
        comprobar(solo_a == "A", f"sin comparar, todos reciben la variante A ({solo_a})")
        nav.js("document.querySelector('#m-comparar').click()")
        time.sleep(0.6)
        varias = nav.js("[...new Set(window.__recontacto.E.lista.filas.filter(f => f.variante).map(f => f.variante))].sort().join('')")
        comprobar(len(varias) >= 2, f"comparando, se reparten varias variantes ({varias})")
        if carpeta:
            nav.foto().save(carpeta / "02_mensajes.png")

        nav.js("document.querySelector('[data-sub=\"respuestas\"]').click()")
        time.sleep(0.8)
        lead = nav.js("document.querySelector('#c-lead').value")
        nav.js("[...document.querySelectorAll('#c-ejemplos button')].find(b => b.dataset.ej === 'Sí, llámame mañana a las 4').click()")
        time.sleep(0.6)
        comprobar("Propone un día u hora" in nav.js("document.querySelector('#c-resultado').textContent"), "interpreta 'sí, llámame mañana a las 4' como una cita")
        comprobar("16:00" in nav.js("document.querySelector('#c-chat').textContent"), "la respuesta sugerida confirma la hora (16:00)")
        nav.js("[...document.querySelectorAll('#c-ejemplos button')].find(b => b.dataset.ej === '¿Cuánto cuesta?').click()")
        time.sleep(0.4)
        comprobar("Pasa a un asesor" in nav.js("document.querySelector('#c-chat').textContent"), "una pregunta de precio pasa a un asesor y no se responde sola")
        nav.js("[...document.querySelectorAll('#c-ejemplos button')].find(b => b.dataset.ej === 'Me siento mal desde ayer').click()")
        time.sleep(0.4)
        comprobar("911" in nav.js("document.querySelector('#c-chat').textContent"), "un malestar se trata como urgencia (911) y no como venta")
        nav.js("[...document.querySelectorAll('#c-ejemplos button')].find(b => b.dataset.ej === 'NO').click()")
        time.sleep(0.4)
        if carpeta:
            nav.foto().save(carpeta / "02_respuestas.png")
        nav.js("document.querySelector('#c-aplicar').click()")
        time.sleep(0.8)
        sigue = nav.js(f"window.__recontacto.E.lista.filas.some(f => f.lead_id === '{lead}')")
        comprobar(sigue is False, f"tras un 'NO' la persona {lead} ya no aparece en la lista")
        comprobar(nav.js("window.__recontacto.E.bajas.size") >= 1, "el 'NO' quedó registrado como baja")
        nav.js("localStorage.removeItem('recontacto_bajas'); window.__recontacto.E.bajas.clear(); window.__recontacto.recalcular()")
        time.sleep(0.5)

        for sub in ("evidencia", "simulacion", "ab", "datos", "limites"):
            nav.js(f"document.querySelector('[data-sub=\"{sub}\"]').click()")
            time.sleep(1.8 if sub in ("evidencia", "simulacion") else 0.8)
            graficas = nav.js(f"document.querySelectorAll('#sub-{sub} .js-plotly-plot').length")
            visibles = nav.js(f"!document.querySelector('#sub-{sub}').hidden")
            comprobar(visibles, f"la subpestaña {sub} se muestra")
            if sub in ("evidencia", "simulacion", "ab"):
                comprobar(graficas >= 1, f"{sub}: {graficas} gráficas interactivas")
            if carpeta:
                nav.foto().save(carpeta / f"02_{sub}.png")
        sim = nav.js("document.querySelector('#s-kpis').textContent")
        comprobar(bool(sim) and "Mejora media" in sim, "la simulación calcula resultados")
        ab = nav.js("document.querySelector('#a-kpis .v').textContent")
        print("  A/B personas por grupo:", ab)
        comprobar(ab.replace(",", "") in ("4094", "4,094"), "prueba A/B: 4,094 por grupo para +3 puntos")

        nav.js("document.querySelector('[data-sub=\"lista\"]').click()")
        time.sleep(0.5)
        nav.js("(() => { const r = document.querySelector('#r-max'); r.value = 2; r.dispatchEvent(new Event('input', {bubbles: true})); })()")
        time.sleep(0.8)
        total = nav.js("document.querySelector('#l-kpis .v').textContent")
        print("  con máximo de 2 intentos:", total)
        comprobar(total == "342", "cambiar una regla recalcula la lista (342, igual que Python)")
        nav.js("(() => { const r = document.querySelector('#r-max'); r.value = 3; r.dispatchEvent(new Event('input', {bubbles: true})); })()")
        time.sleep(0.6)

        nav.js("document.querySelector('[data-sub=\"datos\"]').click()")
        time.sleep(0.4)
        nav.js("document.querySelector('#d-ejemplo').click()")
        time.sleep(1.2)
        informe = nav.js("document.querySelector('#d-informe').textContent")
        comprobar("Nuevas: 2" in informe and "L90001" in informe, "el ejemplo de dos personas muestra informe y decisiones")
        comprobar(nav.js("!document.querySelector('#d-aplicar').disabled"), "'Aplicar cambios' se habilita")
        if carpeta:
            nav.js("document.querySelector('#d-informe').scrollIntoView({block: 'center'})")
            time.sleep(0.4)
            nav.foto().save(carpeta / "03_datos_informe.png")
        nav.js("document.querySelector('#d-aplicar').click()")
        time.sleep(1.2)
        comprobar(nav.js("document.querySelector('#d-kpis .v').textContent") == "1,813", "aplicar agrega las dos personas (1,813 leads)")
        nav.js("document.querySelector('#b-tel').value = '55-02000001'; document.querySelector('#b-boton').click()")
        time.sleep(0.8)
        en_lista = nav.js("window.__recontacto.E.lista.filas.some(f => f.lead_id === 'L90001')")
        comprobar(en_lista is False, "la persona con baja ya no aparece en la lista")
        comprobar(nav.js("window.__recontacto.E.lista.filas.some(f => f.lead_id === 'L90002')") is True, "la otra persona sigue en la lista")
        nav.js("document.querySelector('#d-original').click()")
        time.sleep(0.8)
        comprobar(nav.js("document.querySelector('#d-kpis .v').textContent") == "1,811", "volver a la base original (1,811 leads)")
        nav.js("document.querySelector('#d-informe').innerHTML = ''; document.querySelector('#d-archivo').dispatchEvent(new Event('change'))")

        errores_herramienta = nav.js("JSON.stringify(window.__errs)")
        comprobar(errores_herramienta == "[]", f"la herramienta no tuvo errores de JavaScript ({errores_herramienta})")
        base = url.rsplit("/", 1)[0] + "/"
        esperado = {"index": 5, "memo": 5, "bitacora": 5, "video": 5}
        for pagina in ("index", "memo", "bitacora", "video"):
            nav.ir(base + ("index.html" if pagina == "index" else pagina + ".html"), 1.0)
            enlaces = nav.js("[...document.querySelectorAll('nav.piezas a')].map(a => a.getAttribute('href') + (a.getAttribute('aria-current') ? '*' : '')).join('|')")
            comprobar(len(enlaces.split("|")) == esperado[pagina] and enlaces.count("*") == 1, f"{pagina}: menú con las cuatro entregas y la actual marcada ({enlaces})")
            comprobar(nav.js("document.querySelector('main').textContent.trim().length") > 200, f"{pagina}: tiene contenido")
            if carpeta:
                nav.foto().save(carpeta / f"04_{pagina}.png")
            if pagina == "index":
                comprobar(nav.js("document.querySelectorAll('.entrega a.pildora').length") == 4, "la portada enlaza las cuatro entregas")
            if pagina == "video":
                comprobar(nav.js("document.querySelector('video').getAttribute('src')") == "demo.mp4", "el video apunta a demo.mp4")
                comprobar(nav.js("document.querySelectorAll('.tabla-demos tbody tr').length") == 7, "hay 7 demos para simular")
                comprobar("Pendiente" in nav.js("document.querySelector('.tabla-prueba').textContent"), "la prueba con dos personas aparece como pendiente (sin resultados inventados)")

        errores = nav.js("JSON.stringify(window.__errs)")
        comprobar(errores == "[]", f"sin errores de JavaScript en las demás páginas ({errores})")
    finally:
        nav.cerrar()
    print("\nRESULTADO:", "todo bien" if not fallos else f"{len(fallos)} fallas")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
