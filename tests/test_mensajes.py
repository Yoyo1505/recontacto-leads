import pytest

from recontacto import mensajes


class ClienteFalso:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.recibido = None

    def generar(self, sistema, usuario):
        self.recibido = (sistema, usuario)
        return self.respuesta


BAJA = "Si prefieres que no te escribamos, responde NO."
VALIDO = f"Hola, te escribe Asesor B de Clivi. Intenté comunicarme contigo por tu solicitud de información. Dime si prefieres que te llame o seguir por mensaje. {BAJA}"

CONTEXTOS = [
    {"intento": 1, "nunca_contactado": True, "franja_dia": "hoy por la mañana", "asesor": "Asesor A"},
    {"intento": 2, "nunca_contactado": False, "franja_dia": "el martes por la tarde"},
    {"intento": 3, "nunca_contactado": False, "ultimo_intento": True, "franja_dia": "el jueves por la tarde", "asesor": "Asesor C"},
]


@pytest.mark.parametrize("contexto", CONTEXTOS)
def test_todas_las_plantillas_pasan_la_validacion(contexto):
    texto = mensajes.plantilla(contexto)
    resultado = mensajes.validar_mensaje(texto)
    assert resultado.valido, resultado.problemas


def test_ultimo_intento_avisa_que_no_se_insistira():
    texto = mensajes.plantilla(CONTEXTOS[2])
    assert "último mensaje" in texto


@pytest.mark.parametrize(
    "texto, problema",
    [
        (f"Hola, de Clivi. Sabemos que tienes diabetes y podemos ayudarte. {BAJA}", "menciona la condicion de salud"),
        (f"Hola, de Clivi. Baja de peso rápido. {BAJA}", "menciona la condicion de salud"),
        (f"Hola, de Clivi. Resultados garantizados. {BAJA}", "promete resultados"),
        (f"Hola, de Clivi. Última oportunidad, solo hoy. {BAJA}", "presiona con urgencia"),
        (f"Hola, de Clivi. Entra a https://ejemplo.com. {BAJA}", "incluye enlaces"),
        ("Hola, de Clivi. Te contactamos por tu solicitud.", "no incluye la opcion de baja"),
        (f"Hola, te contactamos por tu solicitud. {BAJA}", "no menciona la marca"),
        ("", "esta vacio"),
        (f"Hola, de Clivi. {'x' * 500} {BAJA}", "es demasiado largo"),
    ],
)
def test_validador_rechaza_mensajes_riesgosos(texto, problema):
    resultado = mensajes.validar_mensaje(texto)
    assert not resultado.valido
    assert problema in resultado.problemas


def test_llm_valido_se_usa():
    cliente = ClienteFalso(VALIDO)
    texto, origen = mensajes.generar_mensaje(CONTEXTOS[1], cliente)
    assert origen == "llm"
    assert texto == VALIDO


def test_llm_invalido_cae_a_la_plantilla():
    cliente = ClienteFalso("Hola, tu diabetes tiene cura garantizada.")
    texto, origen = mensajes.generar_mensaje(CONTEXTOS[1], cliente)
    assert origen == "plantilla"
    assert mensajes.validar_mensaje(texto).valido


def test_llm_sin_respuesta_cae_a_la_plantilla():
    texto, origen = mensajes.generar_mensaje(CONTEXTOS[0], ClienteFalso(None))
    assert origen == "plantilla"


def test_sin_cliente_usa_plantilla():
    _, origen = mensajes.generar_mensaje(CONTEXTOS[0])
    assert origen == "plantilla"


def test_el_contexto_rechaza_datos_personales():
    with pytest.raises(ValueError):
        mensajes.generar_mensaje({"intento": 2, "telefono": "55-01234567"})
    with pytest.raises(ValueError):
        mensajes.construir_prompt({"intento": 2, "edad": 40})


def test_el_prompt_enviado_al_llm_no_contiene_datos_sensibles():
    cliente = ClienteFalso(VALIDO)
    mensajes.generar_mensaje(CONTEXTOS[0], cliente)
    sistema, usuario = cliente.recibido
    assert "55-" not in usuario
    assert set(__import__("json").loads(usuario.splitlines()[0].split(": ", 1)[1])) <= mensajes.CAMPOS_PERMITIDOS
    assert "diabetes" not in usuario.lower()
