import pytest

from recontacto import config, control, ingesta, mensajes
from recontacto.data import cargar_leads
from recontacto.respuestas import aplicar, clasificar

CASOS = [
    ("NO", "baja"),
    ("no", "baja"),
    ("STOP", "baja"),
    ("Dejen de escribirme", "baja"),
    ("no me escriban más", "baja"),
    ("No gracias", "no_interesado"),
    ("Ya no me interesa", "no_interesado"),
    ("sí", "interes"),
    ("Claro que sí", "interes"),
    ("Me interesa", "interes"),
    ("ok", "interes"),
    ("Sí, llámame mañana a las 4", "agenda"),
    ("a las 5 pm", "agenda"),
    ("hoy en la tarde", "agenda"),
    ("mejor el lunes por la mañana", "agenda"),
    ("16:00", "agenda"),
    ("ahorita no puedo", "posponer"),
    ("no puedo hoy", "posponer"),
    ("más tarde", "posponer"),
    ("¿Cuánto cuesta?", "pregunta"),
    ("¿Qué incluye?", "pregunta"),
    ("me siento mal", "seguridad"),
    ("tengo una emergencia", "seguridad"),
    ("jajaja", "ambigua"),
    ("hola", "ambigua"),
    ("", "ambigua"),
]


@pytest.mark.parametrize("texto, esperado", CASOS)
def test_intencion_de_cada_respuesta(texto, esperado):
    assert clasificar(texto).intencion == esperado


def test_no_es_una_baja_y_se_confirma_con_un_texto_fijo():
    c = clasificar("NO")
    assert c.baja and not c.requiere_humano
    assert "no te volveremos a escribir" in c.respuesta_sugerida


def test_las_preguntas_y_lo_ambiguo_pasan_a_un_asesor():
    for texto in ("¿Cuánto cuesta?", "¿Qué incluye el tratamiento?", "jajaja", "me siento mal"):
        c = clasificar(texto)
        assert c.requiere_humano
        if c.intencion in ("pregunta", "ambigua"):
            assert c.respuesta_sugerida == ""


def test_una_cita_con_pregunta_no_se_responde_sola():
    c = clasificar("¿Cuánto cuesta? llámame a las 4")
    assert c.intencion == "agenda" and c.hora == 16
    assert c.requiere_humano and c.respuesta_sugerida == ""


def test_hora_y_dia_se_extraen():
    c = clasificar("Sí, llámame mañana a las 4")
    assert (c.dia, c.hora) == ("mañana", 16)
    assert "mañana a las 16:00" in c.respuesta_sugerida
    assert clasificar("a las 9 am").hora == 9
    assert clasificar("a las 5 p.m.").hora == 17
    assert clasificar("pasado mañana a las 9 am").dia == "pasado mañana"


def test_un_malestar_nunca_se_trata_como_venta():
    c = clasificar("me siento mal, ayuda urgente")
    assert c.intencion == "seguridad" and c.requiere_humano
    assert "911" in c.respuesta_sugerida


def test_aplicar_una_baja_la_registra(entorno):
    c = clasificar("NO")
    assert "baja registrada" in aplicar(c, "L00001", "55-01234567")
    assert config.ARCHIVO_BAJAS.exists()
    assert "ya estaba" in aplicar(c, "L00001", "+52 55 0123 4567")


def test_aplicar_un_interes_cambia_el_estado_sin_borrar_a_nadie(entorno):
    base = cargar_leads(config.ARCHIVO_ORIGINAL)
    lead = base[base["resultado"] == "no_contesta"].iloc[0]
    c = clasificar("sí, llámame mañana a las 4")
    assert "en_seguimiento" in aplicar(c, lead["lead_id"], lead["telefono"])
    nuevo = cargar_leads(config.ruta_datos_activa())
    assert len(nuevo) == len(base)
    assert nuevo.set_index("lead_id").loc[lead["lead_id"], "resultado"] == "en_seguimiento"


def test_aplicar_a_un_lead_inexistente_falla_con_claridad(entorno):
    with pytest.raises(ingesta.ErrorIngesta, match="No existe"):
        aplicar(clasificar("sí"), "L99999", "55-00000000")


def test_cada_variante_es_valida_y_estable():
    for fila in mensajes.biblioteca_validada():
        assert fila["valido"], fila
    assert mensajes.elegir_variante("L00001", "retoma") == mensajes.elegir_variante("L00001", "retoma")


def test_las_variantes_se_reparten_de_forma_pareja():
    conteo = {}
    for i in range(3000):
        v = mensajes.elegir_variante(f"L{i:05d}", "primer_contacto")
        conteo[v] = conteo.get(v, 0) + 1
    assert set(conteo) == {"A", "B", "C"}
    assert all(900 < n < 1100 for n in conteo.values())


def test_la_variante_cambia_el_texto_pero_no_las_reglas():
    base = {"nunca_contactado": True, "asesor": "Asesor A", "franja_dia": "hoy"}
    textos = {v: mensajes.plantilla({**base, "variante": v}) for v in "ABC"}
    assert len(set(textos.values())) == 3
    assert all(mensajes.validar_mensaje(t).valido for t in textos.values())


def test_un_lead_de_agente_de_ia_y_uno_antiguo_cambian_el_saludo():
    texto = mensajes.plantilla({"nunca_contactado": True, "origen_ia": True, "dias": 4, "variante": "A"})
    assert "asistente de inteligencia artificial" in texto and "pasaron unos días" in texto
    assert mensajes.validar_mensaje(texto).valido


def test_el_validador_de_fidelidad_rechaza_lo_que_no_sigue_la_estrategia():
    contexto = {"nunca_contactado": False, "ultimo_intento": False, "variante": "A"}
    suelto = "Hola, te escribimos de Clivi. ¿En qué podemos ayudarte? Si prefieres que no te escribamos, responde NO."
    assert mensajes.validar_mensaje(suelto).valido
    assert not mensajes.validar_mensaje(suelto, contexto).valido
    assert mensajes.validar_mensaje(mensajes.plantilla(contexto), contexto).valido
    de_usted = mensajes.plantilla(contexto).replace("dime si prefieres que te llame", "indique usted si prefiere que le llame")
    assert any("usted" in p for p in mensajes.validar_mensaje(de_usted, contexto).problemas)


def test_comparar_variantes_con_datos_sinteticos(escribir):
    from conftest import fila

    filas = []
    for i in range(400):
        contesto = "en_seguimiento" if (i % 10) < (7 if i % 2 == 0 else 4) else "no_contesta"
        letra = "A" if i % 2 == 0 else "B"
        f = fila(f"L{i:04d}", f"55-{i:08d}", resultado=contesto)
        filas.append(f + [letra])
    ruta = escribir(filas)
    import csv

    with open(ruta, newline="", encoding="utf-8") as archivo:
        lineas = list(csv.reader(archivo))
    lineas[0].append("variante")
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        csv.writer(archivo).writerows(lineas)
    df = cargar_leads(ruta)
    tabla = control.por_variante(df).set_index("variante")
    assert tabla.loc["A", "tasa"] > tabla.loc["B", "tasa"]
    comparacion = control.comparar_variantes(df)
    assert comparacion.loc[0, "variante"] == "B" and comparacion.loc[0, "diferencia"] < 0
    assert bool(comparacion.loc[0, "significativa"])


def test_sin_datos_de_variante_no_hay_comparacion():
    df = cargar_leads(config.ARCHIVO_ORIGINAL)
    assert control.por_variante(df).empty
    assert control.comparar_variantes(df).empty


def test_la_ingesta_conserva_la_variante(entorno):
    import pandas as pd

    crudo = pd.DataFrame([{"lead_id": "L99010", "fecha_registro": "2026-11-08 10:00", "canal": "Meta", "telefono": "55-04000010", "resultado": "no_contesta", "primer_contacto": "2026-11-08 12:00", "variante": "B"}])
    informe = ingesta.aplicar(ingesta.procesar(crudo))
    assert informe.aplicado
    assert "variante" in config.ARCHIVO_ACTUAL.read_text(encoding="utf-8").splitlines()[0]
    guardado = cargar_leads(config.ruta_datos_activa())
    assert guardado.set_index("lead_id").loc["L99010", "variante"] == "B"
