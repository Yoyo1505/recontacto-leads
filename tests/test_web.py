import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="Node.js no esta instalado")
def test_el_motor_web_coincide_con_python():
    resultado = subprocess.run([NODE, str(RAIZ / "web" / "prueba_motor.js")], capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "coincide con Python" in resultado.stdout


def test_cada_entrega_tiene_su_pagina_sin_marcadores_pendientes():
    sitio = RAIZ / "web" / "sitio"
    esperado = {
        "herramienta": ("vista-herramienta", "datos-json", "memo.html", "bitacora.html", "video.html"),
        "memo": ("Entrega 2", "Qué no funciona todavía"),
        "bitacora": ("Entrega 3", "Uso de IA"),
        "video": ("Entrega 4", "Demos para simular", "Prueba con dos personas", "demo.mp4"),
    }
    for nombre, marcas in esperado.items():
        pagina = (sitio / f"{nombre}.html").read_text(encoding="utf-8")
        assert "{{" not in pagina, nombre
        for marca in marcas:
            assert marca.lower() in pagina.lower(), (nombre, marca)
        assert pagina.count(' aria-current="page">') == 1, nombre
    redireccion = (sitio / "index.html").read_text(encoding="utf-8")
    assert "herramienta.html" in redireccion and len(redireccion) < 1000
    assert "plotly" not in (sitio / "memo.html").read_text(encoding="utf-8").lower()


def test_los_archivos_ensamblados_coinciden_con_las_secciones_de_web_fuente():
    resultado = subprocess.run(["python", str(RAIZ / "scripts" / "ensamblar_web.py"), "--revisar"], capture_output=True, text=True, encoding="utf-8")
    assert resultado.returncode == 0, resultado.stdout


def test_cada_seccion_web_empieza_con_su_marca_y_tiene_numero_unico():
    for carpeta in ("motor", "app"):
        partes = sorted((RAIZ / "web" / "fuente" / carpeta).glob("[0-9][0-9]_*.js"))
        numeros = [p.name[:2] for p in partes]
        assert len(numeros) == len(set(numeros)) and len(partes) >= 8
        for parte in partes[1:-1]:
            assert parte.read_text(encoding="utf-8").startswith("  // ------"), parte.name
