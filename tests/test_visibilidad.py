import pandas as pd
import pytest

from recontacto import visibilidad as v

RAIZ = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_una_respuesta_sin_la_marca_esta_ausente():
    r = v.puntuar("Te recomiendo consultar a un endocrinólogo en un consultorio cercano.")
    assert not r["menciona"] and r["encuadre"] == "ausente" and not r["primero"]


def test_recomendacion_primero_y_con_enlace():
    r = v.puntuar("Te recomiendo Clivi: una clínica digital con médicos. Más en https://www.clivi.com.mx/obesidad")
    assert r["menciona"] and r["primero"] and r["encuadre"] == "recomendacion" and r["cita"]


def test_una_alternativa_no_cuenta_como_recomendacion():
    r = v.puntuar("La mejor opción es un consultorio presencial. Como alternativa, Clivi ofrece atención en línea.")
    assert r["menciona"] and r["encuadre"] == "alternativa"


def test_una_mencion_neutra():
    r = v.puntuar("Existen varias clínicas digitales en México, entre ellas Clivi y otras.")
    assert r["encuadre"] == "mencion"


def test_mencion_tardia_no_es_primera():
    r = v.puntuar("x " * 200 + "Clivi")
    assert r["menciona"] and not r["primero"]


def test_detecta_cifras_contradictorias_y_advertencias():
    r = v.puntuar("Clivi tiene más de 20 mil pacientes y más de 10,000 tratados. Cuidado con las quejas.")
    assert r["cifras"] == "10 mil, 20 mil" and r["negativo"]


def test_resumen_por_motor_con_intervalos():
    filas = [
        {"motor": "a", "respuesta": "Te recomiendo Clivi."},
        {"motor": "a", "respuesta": "Consulta un especialista."},
        {"motor": "b", "respuesta": "Como alternativa, Clivi."},
        {"motor": "b", "respuesta": "Clivi es la solución ideal."},
    ]
    t = v.resumir(filas).set_index("motor")
    assert t.loc["a", "menciona"] == 1 and t.loc["a", "recomendacion"] == 1
    assert t.loc["b", "alternativa"] == 1 and t.loc["b", "recomendacion"] == 1
    assert "a" in t.loc["a", "menciona_ic"] or "%" in t.loc["a", "menciona_ic"]


def test_plantilla_de_preguntas_y_linea_de_comandos(tmp_path, capsys):
    prompts = RAIZ / "docs" / "panel_visibilidad_prompts.csv"
    salida = tmp_path / "respuestas.csv"
    assert v.main(["--plantilla", str(prompts), "--salida", str(salida)]) == 0
    tabla = pd.read_csv(salida, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert {"motor", "prompt_id", "prompt", "respuesta"} <= set(tabla.columns)
    assert tabla["motor"].nunique() == 4 and len(tabla) == 4 * len(pd.read_csv(prompts))
    assert v.main(["--respuestas", str(salida)]) == 1
    tabla.loc[0, "respuesta"] = "Te recomiendo Clivi."
    tabla.to_csv(salida, index=False, encoding="utf-8-sig")
    assert v.main(["--respuestas", str(salida)]) == 0
    assert "chatgpt" in capsys.readouterr().out


def test_las_preguntas_del_panel_no_mencionan_a_la_marca():
    prompts = pd.read_csv(RAIZ / "docs" / "panel_visibilidad_prompts.csv", encoding="utf-8-sig")
    assert len(prompts) >= 30
    assert not prompts["prompt"].str.lower().str.contains("clivi").any()
    assert prompts["categoria"].nunique() >= 5
