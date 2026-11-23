import base64
import json
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))

from contexto import Contexto, estado_inicial, reglas_a_dict, reglas_desde_dict  # noqa: E402
from dash_app import crear_app  # noqa: E402
from secciones import POR_RUTA, SECCIONES  # noqa: E402
from secciones import evidencia, lista, prueba_ab, resumen, simulacion  # noqa: E402

from recontacto import config  # noqa: E402
from recontacto import simulacion as sim  # noqa: E402


@pytest.fixture(scope="module")
def ctx():
    return Contexto(config.ARCHIVO_ORIGINAL)


@pytest.fixture(scope="module")
def app(ctx):
    return crear_app(ctx)


def test_reglas_ida_y_vuelta():
    assert reglas_desde_dict(reglas_a_dict(config.REGLAS)) == config.REGLAS


def test_el_estado_inicial_es_serializable():
    json.dumps(estado_inicial())


def test_las_rutas_de_las_secciones_son_unicas():
    assert len(POR_RUTA) == len(SECCIONES)
    assert POR_RUTA["/"] is resumen


@pytest.mark.parametrize("seccion", SECCIONES, ids=lambda s: s.ID)
def test_cada_seccion_tiene_la_interfaz_comun(seccion, ctx):
    assert seccion.ID and seccion.TITULO and seccion.RUTA.startswith("/")
    assert len(seccion.layout(ctx)) > 0
    assert callable(seccion.registrar)


def test_la_app_sirve_el_logo_y_los_estilos(app):
    cliente = app.server.test_client()
    assert cliente.get("/").status_code == 200
    assert cliente.get("/assets/logo-clivi.png").status_code == 200
    assert cliente.get("/assets/estilo.css").status_code == 200


def test_figuras_de_resumen(ctx):
    for fig in (resumen.figura_embudo(ctx.df), resumen.figura_no_contesta_canal(ctx.df)):
        assert isinstance(fig, go.Figure) and len(fig.data) >= 1


def test_embudo_es_decreciente(ctx):
    valores = list(resumen.figura_embudo(ctx.df).data[0].x)
    assert valores == sorted(valores, reverse=True)


def test_figuras_de_evidencia(ctx):
    resultados = ctx.evaluacion[0]
    figuras = [evidencia.figura_tasas(ctx.X, ctx.y, d) for d in evidencia.DIMENSIONES]
    figuras += [
        evidencia.figura_confusion(ctx.X, ctx.y),
        evidencia.figura_ablacion(resultados),
        evidencia.figura_calibracion(resultados),
        evidencia.figura_carta_p(ctx.df),
        evidencia.figura_embudo_asesores(ctx.df),
    ]
    assert all(isinstance(f, go.Figure) and len(f.data) >= 1 for f in figuras)


def test_los_ejes_de_categorias_no_se_interpretan_como_fechas(ctx):
    assert evidencia.figura_tasas(ctx.X, ctx.y, "franja_hora").layout.xaxis.type == "category"


def test_figuras_de_lista_con_lista_vacia(ctx):
    vacia = ctx.lista(estado_inicial())[0].iloc[0:0]
    assert isinstance(lista.figura_mapa_calor(vacia), go.Figure)
    assert lista.filas_tabla(vacia) == []
    assert lista.filtrar(ctx.lista(estado_inicial())[0], [], False).empty


def test_filtro_de_nuevos_solo_deja_nunca_contactados(ctx):
    todo = ctx.lista(estado_inicial())[0]
    solo = lista.filtrar(todo, list(todo["canal"].unique()), True)
    assert len(solo) > 0 and solo["nunca_contactado"].all()


def test_etiqueta_de_horario():
    assert lista.etiqueta_horario(pd.Timestamp("2026-11-09 09:00")) == "lun 09/11 09:00"
    assert lista.etiqueta_horario(pd.NaT) == "sin horario"


def test_interpretacion_de_la_simulacion_distingue_si_el_intervalo_cruza_el_cero():
    cruza = {"media": 5, "ic_bajo": -10, "ic_alto": 20, "prob_mejora": 0.7}
    no_cruza = {"media": 15, "ic_bajo": 4, "ic_alto": 25, "prob_mejora": 0.99}
    assert "incluye el cero" in simulacion.interpretar(cruza, 0.5, 300)
    assert "no incluye el cero" in simulacion.interpretar(no_cruza, 1.0, 300)


def test_figuras_de_simulacion_y_ab(ctx):
    prep = ctx.preparacion(estado_inicial())
    corridas = sim.simular(prep, 0.5, 300)
    r = sim.resumen(corridas)
    assert isinstance(simulacion.figura_histograma(corridas, r), go.Figure)
    assert isinstance(simulacion.figura_tasas(corridas), go.Figure)
    assert isinstance(simulacion.figura_sensibilidad(sim.sensibilidad_alpha(prep, n_sim=100), 0.5), go.Figure)
    assert isinstance(prueba_ab.figura_potencia(0.6, 0.05, 4000), go.Figure)
    assert len(prueba_ab.tabla_tamanos(0.6, 0.05, 41)) == len(prueba_ab.EFECTOS)


def _valores(ctx):
    estado = estado_inicial()
    filas = lista.filas_tabla(ctx.lista(estado)[0])[:3]
    return {
        "ctl-fecha.date": "2026-11-09",
        "ctl-horas.value": [9, 20],
        "ctl-dias.value": [0, 1, 2, 3, 4, 5],
        "ctl-intentos.value": 3,
        "ctl-entre.value": 24,
        "ctl-ventana.value": 21,
        "ctl-capacidad.value": 15,
        "estado.data": estado,
        "filtro-canales.value": sorted(ctx.df["canal"].unique()),
        "filtro-nuevos.value": [],
        "tabla-lista.derived_virtual_selected_rows": [0],
        "tabla-lista.derived_virtual_data": filas,
        "boton-descarga.n_clicks": 1,
        "selector-dimension.value": "canal",
        "sim-alpha.value": 0.5,
        "sim-n.value": 500,
        "ab-efecto.value": 3,
        "ab-alfa.value": 0.05,
        "ab-potencia.value": 0.8,
        "ab-flujo.value": 41,
        "datos-subir.contents": None,
        "datos-subir.filename": None,
        "form-revisar.n_clicks": None,
        "form-canal.value": "Agente IA",
        "form-objetivo.value": "control de peso",
        "form-plan.value": 1599,
        "form-edad.value": 38,
        "form-telefono.value": "55-05000001",
        "form-entidad.value": "CDMX",
        "form-fecha.value": "2026-11-08 20:00",
        "form-resultado.value": "sin_contactar",
        "form-contacto.value": "",
        "datos-aplicar.n_clicks": 0,
        "baja-boton.n_clicks": 1,
        "baja-telefono.value": "",
        "version-restaurar.n_clicks": 1,
        "version-original.n_clicks": None,
        "version-lista.value": None,
    }


def _carga(clave, definicion, valores, cambiado=None):
    def entradas(lista_):
        return [{"id": i["id"], "property": i["property"], "value": valores[f"{i['id']}.{i['property']}"]} for i in lista_]

    tokens = clave.strip(".").split("...")
    salidas = [{"id": t.rsplit(".", 1)[0], "property": t.rsplit(".", 1)[1]} for t in tokens]
    if len(tokens) == 1 and not clave.startswith(".."):
        salidas = salidas[0]
    carga = {
        "output": clave,
        "outputs": salidas,
        "inputs": entradas(definicion["inputs"]),
        "changedPropIds": [cambiado or f"{definicion['inputs'][0]['id']}.{definicion['inputs'][0]['property']}"],
    }
    if definicion["state"]:
        carga["state"] = entradas(definicion["state"])
    return carga


def test_todos_los_callbacks_responden_sin_error(app, ctx):
    valores = _valores(ctx)
    cliente = app.server.test_client()
    sin_cubrir = []
    for clave, definicion in app.callback_map.items():
        if clave.startswith("..contenido.children"):
            continue
        ids = [f"{i['id']}.{i['property']}" for i in definicion["inputs"] + definicion["state"]]
        if any(i not in valores for i in ids):
            sin_cubrir.append(clave)
            continue
        respuesta = cliente.post("/_dash-update-component", json=_carga(clave, definicion, valores))
        assert respuesta.status_code == 200, f"{clave}: {respuesta.data[:300]}"
    assert not sin_cubrir, f"Callbacks sin valores de prueba: {sin_cubrir}"


@pytest.mark.parametrize("ruta", list(POR_RUTA))
def test_el_enrutamiento_carga_cada_seccion(app, ctx, ruta):
    definicion = app.callback_map["..contenido.children...menu.children.."]
    carga = _carga("..contenido.children...menu.children..", definicion, {"url.pathname": ruta})
    respuesta = app.server.test_client().post("/_dash-update-component", json=carga)
    assert respuesta.status_code == 200


def test_reglas_invalidas_muestran_error_y_no_cambian_el_estado(app, ctx):
    clave = "..estado.data...ctl-error.children.."
    valores = _valores(ctx)
    valores["ctl-dias.value"] = []
    respuesta = app.server.test_client().post("/_dash-update-component", json=_carga(clave, app.callback_map[clave], valores))
    cuerpo = respuesta.get_json()["response"]
    assert "no válidas" in cuerpo["ctl-error"]["children"]
    assert "estado" not in cuerpo or "data" not in cuerpo.get("estado", {})


def _clave(app, salidas):
    objetivo = "..." .join(salidas)
    for clave in app.callback_map:
        if re.sub(r"@[0-9a-f]+", "", clave.strip(".")) == objetivo:
            return clave
    raise KeyError(objetivo)


def _llamar(app, salidas, valores, cambiado):
    clave = _clave(app, salidas)
    respuesta = app.server.test_client().post("/_dash-update-component", json=_carga(clave, app.callback_map[clave], valores, cambiado))
    assert respuesta.status_code == 200, respuesta.data[:400]
    return respuesta.get_json()["response"]


def test_flujo_completo_de_datos_en_la_app(entorno):
    ctx2 = Contexto()
    app2 = crear_app(ctx2)
    valores = _valores(ctx2)
    assert len(ctx2.df) == 1811

    csv = (RAIZ / "data" / "ejemplos" / "dos_personas_nuevas.csv").read_bytes()
    valores["datos-subir.contents"] = "data:text/csv;base64," + base64.b64encode(csv).decode()
    valores["datos-subir.filename"] = "dos_personas_nuevas.csv"
    revisar = ["datos-informe.children", "datos-aplicar.disabled", "datos-mensaje-aplicar.children"]
    r = _llamar(app2, revisar, valores, "datos-subir.contents")
    assert "Nuevas: 2" in json.dumps(r["datos-informe"]["children"])
    assert r["datos-aplicar"]["disabled"] is False
    assert not config.ARCHIVO_ACTUAL.exists()

    valores["datos-aplicar.n_clicks"] = 1
    aplicar = ["datos-mensaje-aplicar.children", "datos-aplicar.disabled", "estado.data", "ctl-fecha.date"]
    r = _llamar(app2, aplicar, valores, "datos-aplicar.n_clicks")
    assert len(ctx2.df) == 1813 and config.ARCHIVO_ACTUAL.exists()
    assert set(ctx2.ids_nuevos) == {"L90001", "L90002"}
    assert r["estado"]["data"]["version"] == ctx2.version

    valores["estado.data"] = r["estado"]["data"]
    valores["baja-telefono.value"] = "55-02000001"
    r = _llamar(app2, ["baja-mensaje.children", "estado.data", "ctl-fecha.date"], valores, "baja-boton.n_clicks")
    lista, excluidos = ctx2.lista(r["estado"]["data"])
    assert "L90001" not in set(lista["lead_id"])
    assert excluidos.set_index("lead_id").loc["L90001", "motivo_exclusion"] == "baja"
    assert "L90002" in set(lista["lead_id"])

    valores["estado.data"] = r["estado"]["data"]
    r = _llamar(app2, ["version-mensaje.children", "estado.data", "ctl-fecha.date"], valores, "version-original.n_clicks")
    assert len(ctx2.df) == 1811 and ctx2.n_bajas == 1


def test_un_archivo_invalido_no_cambia_nada_y_explica_por_que(entorno):
    ctx2 = Contexto()
    app2 = crear_app(ctx2)
    valores = _valores(ctx2)
    valores["datos-subir.contents"] = "data:text/csv;base64," + base64.b64encode(b"a,b" + bytes([10]) + b"1,2" + bytes([10])).decode()
    valores["datos-subir.filename"] = "malo.csv"
    r = _llamar(app2, ["datos-informe.children", "datos-aplicar.disabled", "datos-mensaje-aplicar.children"], valores, "datos-subir.contents")
    assert "Faltan columnas obligatorias" in json.dumps(r["datos-informe"]["children"])
    assert r["datos-aplicar"]["disabled"] is True
    assert not config.ARCHIVO_ACTUAL.exists()


def test_formulario_de_una_persona(entorno):
    ctx2 = Contexto()
    app2 = crear_app(ctx2)
    valores = _valores(ctx2)
    valores["form-revisar.n_clicks"] = 1
    r = _llamar(app2, ["datos-informe.children", "datos-aplicar.disabled", "datos-mensaje-aplicar.children"], valores, "form-revisar.n_clicks")
    assert "Nuevas: 1" in json.dumps(r["datos-informe"]["children"]) and r["datos-aplicar"]["disabled"] is False
    valores["form-telefono.value"] = "12"
    r = _llamar(app2, ["datos-informe.children", "datos-aplicar.disabled", "datos-mensaje-aplicar.children"], valores, "form-revisar.n_clicks")
    assert "telefono no valido" in json.dumps(r["datos-informe"]["children"]) and r["datos-aplicar"]["disabled"] is True
