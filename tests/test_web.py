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


def test_la_pagina_de_entrega_esta_armada_sin_marcadores_pendientes():
    pagina = (RAIZ / "web" / "entrega.html").read_text(encoding="utf-8")
    assert "{{" not in pagina
    for pieza in ("Memo de una página", "Bitácora", "Video demo", "Prueba con dos personas", "demo.mp4"):
        assert pieza in pagina


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
