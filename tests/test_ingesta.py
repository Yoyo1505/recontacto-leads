import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd
import pytest
from conftest import fila

from recontacto import config, ingesta, policy
from recontacto.data import cargar_leads, clave_telefono, enriquecer

EJEMPLOS = config.DATOS / "ejemplos"
NUEVOS = {
    "csv": EJEMPLOS / "dos_personas_nuevas.csv",
    "json": EJEMPLOS / "dos_personas_nuevas.json",
    "xlsx": EJEMPLOS / "dos_personas_nuevas.xlsx",
    "parquet": EJEMPLOS / "dos_personas_nuevas.parquet",
}


def crudo(**cambios):
    base = {
        "lead_id": "L99001", "fecha_registro": "2026-11-08 10:00", "canal": "meta", "anuncio": "", "estado": "CDMX",
        "edad": "40", "objetivo": "control de peso", "plan_de_interes": "1299", "telefono": "55-03000001",
        "asesor": "", "primer_contacto": "", "resultado": "sin_contactar", "monto_venta": "",
    }
    base.update(cambios)
    return pd.DataFrame([base])


@pytest.mark.parametrize("formato", NUEVOS)
def test_todos_los_formatos_dan_las_mismas_personas(formato):
    tabla, _ = ingesta.leer_fuente(str(NUEVOS[formato]))
    informe = ingesta.procesar(tabla)
    assert informe.validos == 2 and len(informe.rechazados) == 0
    assert sorted(informe.agregados) == ["L90001", "L90002"]


def test_sqlite_y_cadena_de_conexion(tmp_path):
    from sqlalchemy import create_engine

    ruta = tmp_path / "leads.db"
    pd.read_csv(NUEVOS["csv"], dtype=str, keep_default_na=False).to_sql("leads", create_engine(f"sqlite:///{ruta.as_posix()}"), index=False)
    por_archivo, _ = ingesta.leer_fuente(str(ruta))
    por_url, _ = ingesta.leer_fuente(f"sqlite:///{ruta.as_posix()}", tabla="leads")
    por_consulta, _ = ingesta.leer_fuente(f"sqlite:///{ruta.as_posix()}", consulta="SELECT * FROM leads WHERE canal = 'Meta'")
    assert len(por_archivo) == 2 and len(por_url) == 2 and len(por_consulta) == 1


def test_origen_desde_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("FUENTE_PRUEBA", str(NUEVOS["csv"]))
    tabla, _ = ingesta.leer_fuente("env:FUENTE_PRUEBA")
    assert len(tabla) == 2
    with pytest.raises(ingesta.ErrorIngesta, match="no esta definida"):
        ingesta.leer_fuente("env:NO_EXISTE_ESTA_VARIABLE")


@pytest.mark.parametrize(
    "consulta",
    ["DROP TABLE leads", "SELECT * FROM leads; DROP TABLE leads", "DELETE FROM leads", "SELECT 1; SELECT 2", "UPDATE leads SET canal='x'"],
)
def test_las_consultas_que_modifican_datos_se_rechazan(tmp_path, consulta):
    with pytest.raises(ingesta.ErrorIngesta, match="solo lectura"):
        ingesta._leer_base_de_datos(f"sqlite:///{(tmp_path / 'x.db').as_posix()}", None, consulta)


def test_nombre_de_tabla_invalido(tmp_path):
    with pytest.raises(ingesta.ErrorIngesta, match="no valido"):
        ingesta._leer_base_de_datos(f"sqlite:///{(tmp_path / 'x.db').as_posix()}", "leads; DROP TABLE x", None)


def test_descarga_por_http():
    manejador = partial(SimpleHTTPRequestHandler, directory=str(EJEMPLOS))
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        tabla, _ = ingesta.leer_fuente(f"http://127.0.0.1:{servidor.server_port}/dos_personas_nuevas.csv")
    finally:
        servidor.shutdown()
    assert len(tabla) == 2


def test_descarga_fallida_no_expone_secretos():
    with pytest.raises(ingesta.ErrorIngesta) as error:
        ingesta.leer_fuente("http://usuario:clave_secreta@127.0.0.1:9/x.csv?token=abc123")
    assert "clave_secreta" not in str(error.value) and "abc123" not in str(error.value)


def test_nube_sin_libreria_da_instrucciones():
    with pytest.raises(ingesta.ErrorIngesta, match="s3fs|credenciales|descargar"):
        ingesta.leer_fuente("s3://bucket-que-no-existe/leads.csv")


def test_formato_no_soportado_y_archivo_inexistente(tmp_path):
    with pytest.raises(ingesta.ErrorIngesta, match="Formato no soportado"):
        ingesta.leer_bytes("datos.docx", b"x")
    with pytest.raises(ingesta.ErrorIngesta, match="No existe"):
        ingesta.leer_fuente(str(tmp_path / "no_existe.csv"))


def test_json_como_objeto_con_lista():
    datos = json.dumps({"leads": crudo().to_dict("records")}).encode()
    assert len(ingesta.leer_bytes("x.json", datos)) == 1


def test_enmascarar_oculta_secretos():
    assert "secreto123" not in ingesta.enmascarar("postgresql://usuario:secreto123@host/db")
    assert "abc" not in ingesta.enmascarar("https://x.com/a.csv?token=abc&y=1")


def test_sinonimos_de_columnas():
    tabla = pd.DataFrame(
        [{"ID": "L1", "Fecha": "2026-11-08 10:00", "Fuente": "Google", "Celular": "5512345678", "Status": "Sin contactar", "Columna rara": "x"}]
    )
    texto, mapeo, ignoradas = ingesta.normalizar_columnas(tabla)
    assert mapeo["telefono"] == "Celular" and mapeo["lead_id"] == "ID"
    assert ignoradas == ["Columna rara"]
    assert texto.loc[0, "resultado"] == "Sin contactar"


def test_faltan_columnas_obligatorias():
    tabla = pd.DataFrame([{"lead_id": "L1", "fecha_registro": "2026-11-08", "canal": "Meta", "resultado": "venta"}])
    with pytest.raises(ingesta.ErrorIngesta, match="telefono"):
        ingesta.normalizar_columnas(tabla)


@pytest.mark.parametrize(
    "cambios, motivo",
    [
        ({"lead_id": ""}, "lead_id vacio"),
        ({"fecha_registro": "ayer"}, "fecha_registro no valida"),
        ({"canal": ""}, "canal vacio"),
        ({"telefono": "123"}, "telefono no valido"),
        ({"resultado": "quien sabe"}, "resultado desconocido"),
        ({"primer_contacto": "mañana"}, "primer_contacto no valido"),
    ],
)
def test_filas_invalidas_se_rechazan_con_motivo(cambios, motivo):
    texto, _, _ = ingesta.normalizar_columnas(crudo(**cambios))
    validos, rechazados, _ = ingesta.validar(texto)
    assert len(validos) == 0 and motivo in rechazados.iloc[0]["motivo"]


def test_lead_id_repetido_en_el_archivo():
    texto, _, _ = ingesta.normalizar_columnas(pd.concat([crudo(), crudo(telefono="55-03000002")]))
    validos, rechazados, _ = ingesta.validar(texto)
    assert len(validos) == 1 and "repetido" in rechazados.iloc[0]["motivo"]


def test_advertencias_no_rechazan_la_fila():
    texto, _, _ = ingesta.normalizar_columnas(crudo(edad="199", resultado="venta", monto_venta="", primer_contacto="2026-11-07 09:00"))
    validos, rechazados, avisos = ingesta.validar(texto)
    mensajes = " | ".join(m for _, m in avisos)
    assert len(validos) == 1 and len(rechazados) == 0
    assert "edad" in mensajes and "venta sin monto" in mensajes and "anterior al registro" in mensajes
    assert pd.isna(validos.loc[0, "edad"])


def test_el_canal_se_normaliza_y_los_nuevos_se_respetan():
    nuevos = pd.concat([crudo(canal="tiktok"), crudo(lead_id="L99002", telefono="55-03000002", canal="Agente IA")])
    validos, _, _ = ingesta.validar(ingesta.normalizar_columnas(nuevos)[0])
    assert validos["canal"].tolist() == ["TikTok", "Agente IA"]


def test_fechas_de_excel_y_formatos_distintos():
    tabla = crudo(fecha_registro=pd.Timestamp("2026-11-08 10:00"))
    tabla.loc[0, "primer_contacto"] = "09/11/2026 08:30"
    informe = ingesta.procesar(tabla)
    assert informe.validos == 1
    assert informe.fusionado.set_index("lead_id").loc["L99001", "primer_contacto"] == pd.Timestamp("2026-11-09 08:30")


def test_fusion_agrega_actualiza_y_no_borra():
    base = ingesta.leer_canonico(config.ARCHIVO_ORIGINAL)
    existente = base.iloc[0]
    cambio = crudo(
        lead_id=existente["lead_id"], telefono=existente["telefono"], fecha_registro=str(existente["fecha_registro"])[:16],
        canal=existente["canal"], resultado="venta", monto_venta="1299",
    )
    informe = ingesta.procesar(pd.concat([cambio, crudo()]), base=base)
    assert informe.agregados == ["L99001"]
    assert "resultado" in informe.actualizados[existente["lead_id"]]
    assert len(informe.fusionado) == len(base) + 1


def test_mismo_lead_con_otro_telefono_es_un_conflicto():
    base = ingesta.leer_canonico(config.ARCHIVO_ORIGINAL)
    existente = base.iloc[0]
    informe = ingesta.procesar(crudo(lead_id=existente["lead_id"], telefono="55-09999999"), base=base)
    assert informe.conflictos == [existente["lead_id"]]
    assert not informe.hay_cambios
    assert "otro telefono" in informe.rechazados.iloc[0]["motivo"]


def test_un_archivo_igual_a_la_base_no_cambia_nada():
    base = ingesta.leer_canonico(config.ARCHIVO_ORIGINAL)
    original = pd.read_csv(config.ARCHIVO_ORIGINAL, dtype=str, keep_default_na=False)
    informe = ingesta.procesar(original, base=base)
    assert not informe.hay_cambios and informe.sin_cambio == len(base)


def test_sin_aplicar_no_se_guarda_nada(entorno):
    ingesta.procesar(crudo())
    assert not config.ARCHIVO_ACTUAL.exists()


def test_aplicar_guarda_versiona_y_se_puede_restaurar(entorno):
    primero = ingesta.aplicar(ingesta.procesar(crudo()))
    assert primero.version_guardada is None and config.ARCHIVO_ACTUAL.exists()
    assert len(cargar_leads(config.ruta_datos_activa())) == 1812
    segundo = ingesta.aplicar(ingesta.procesar(crudo(lead_id="L99002", telefono="55-03000002")))
    assert segundo.version_guardada in ingesta.listar_versiones()
    assert len(cargar_leads(config.ruta_datos_activa())) == 1813
    ingesta.restaurar()
    assert len(cargar_leads(config.ruta_datos_activa())) == 1812
    assert ingesta.restaurar("original") == "original"
    assert not config.ARCHIVO_ACTUAL.exists() and len(cargar_leads(config.ruta_datos_activa())) == 1811


def test_restaurar_sin_versiones_o_con_nombre_inexistente(entorno):
    with pytest.raises(ingesta.ErrorIngesta, match="No hay versiones"):
        ingesta.restaurar()
    ingesta.aplicar(ingesta.procesar(crudo()))
    ingesta.aplicar(ingesta.procesar(crudo(lead_id="L99002", telefono="55-03000002")))
    with pytest.raises(ingesta.ErrorIngesta, match="No existe la version"):
        ingesta.restaurar("leads_inexistente.csv")


def test_solo_se_conservan_las_ultimas_versiones(entorno, monkeypatch):
    monkeypatch.setattr(config, "VERSIONES_A_CONSERVAR", 2)
    for i in range(5):
        ingesta.aplicar(ingesta.procesar(crudo(lead_id=f"L9910{i}", telefono=f"55-0300010{i}")))
    assert len(ingesta.listar_versiones()) == 2


def test_las_filas_rechazadas_se_guardan_para_revisarlas(entorno):
    informe = ingesta.aplicar(ingesta.procesar(pd.concat([crudo(), crudo(lead_id="L99002", telefono="1")])))
    guardados = list((entorno / "salidas").glob("rechazados_*.csv"))
    assert len(guardados) == 1 and "telefono no valido" in guardados[0].read_text(encoding="utf-8-sig")
    assert informe.validos == 1


def test_el_csv_guardado_conserva_el_formato_original(entorno):
    ingesta.aplicar(ingesta.procesar(crudo()))
    texto = config.ARCHIVO_ACTUAL.read_text(encoding="utf-8")
    assert texto.splitlines()[0] == ",".join(ingesta.COLUMNAS)
    assert "L99001,2026-11-08 10:00,Meta" in texto


def test_el_telefono_se_reconoce_aunque_cambie_el_formato():
    assert clave_telefono("+52 55 0152 1432") == clave_telefono("55-01521432") == "5501521432"
    assert clave_telefono(None) == ""


def test_la_misma_persona_con_otro_formato_de_telefono_cuenta_como_repetida(escribir):
    filas = [fila("L1", "55-01000001"), fila("L2", "+52 55 0100 0001", fecha="2026-10-05 10:00", contacto="2026-10-05 11:00")]
    assert cargar_leads(escribir(filas))["es_duplicado"].tolist() == [False, True]


def test_baja_es_idempotente_y_valida(entorno):
    assert ingesta.agregar_baja("55-03000001") is True
    assert ingesta.agregar_baja("+52 55 0300 0001") is False
    with pytest.raises(ingesta.ErrorIngesta):
        ingesta.agregar_baja("12")


def test_quien_pidio_baja_no_recibe_mensajes(escribir):
    ruta = escribir(
        [
            fila("L1", "55-01000001", fecha="2026-11-07 10:00", contacto="2026-11-07 11:00"),
            fila("L2", "55-01000002", fecha="2026-11-07 10:00", contacto="2026-11-07 11:00"),
        ]
    )
    df = cargar_leads(ruta, bajas=["5501000001"])
    motivos = policy.evaluar_elegibilidad(df, pd.Timestamp("2026-11-09 08:00")).set_index("lead_id")["motivo_exclusion"]
    assert motivos["L1"] == "baja" and pd.isna(motivos["L2"])


def test_columna_baja_en_los_datos_tambien_se_respeta(escribir):
    df = cargar_leads(escribir([fila("L1", "55-01000001", fecha="2026-11-07 10:00", contacto="2026-11-07 11:00")]))
    df["baja"] = "si"
    assert enriquecer(df)["en_lista_bajas"].all()


def test_que_pasaria_con_dos_personas_nuevas(entorno):
    tabla, _ = ingesta.leer_fuente(str(NUEVOS["csv"]))
    decisiones = ingesta.simular_llegada(ingesta.procesar(tabla)).set_index("lead_id")
    assert decisiones.loc["L90001", "decision"] == "contactar"
    assert decisiones.loc["L90001", "horario"].date() == pd.Timestamp("2026-11-09").date()
    assert "Nunca fue contactado" in decisiones.loc["L90001", "motivo"]
    assert decisiones.loc["L90002", "decision"] == "contactar"
    assert decisiones.loc["L90002", "horario"] >= pd.Timestamp("2026-11-09 10:20")
    assert "responde NO" in decisiones.loc["L90001", "mensaje"]
    assert not config.ARCHIVO_ACTUAL.exists()


def test_una_persona_nueva_que_ya_pidio_baja_no_se_contacta(entorno):
    ingesta.agregar_baja("55-02000001")
    tabla, _ = ingesta.leer_fuente(str(NUEVOS["csv"]))
    decisiones = ingesta.simular_llegada(ingesta.procesar(tabla)).set_index("lead_id")
    assert decisiones.loc["L90001", "decision"] == "no contactar"
    assert "no recibir" in decisiones.loc["L90001", "motivo"]


def test_una_persona_nueva_que_ya_es_cliente_no_se_contacta(entorno):
    base = ingesta.leer_canonico(config.ARCHIVO_ORIGINAL)
    cliente = base[base["resultado"] == "venta"].iloc[0]
    nueva = crudo(lead_id="L99050", telefono=cliente["telefono"], fecha_registro="2026-11-08 20:00")
    decisiones = ingesta.simular_llegada(ingesta.procesar(nueva, base=base)).set_index("lead_id")
    assert decisiones.loc["L99050", "decision"] == "no contactar"


def test_linea_de_comandos(entorno, capsys):
    assert ingesta.main(["--origen", str(NUEVOS["csv"])]) == 0
    assert "No se guardo nada" in capsys.readouterr().out
    assert not config.ARCHIVO_ACTUAL.exists()
    assert ingesta.main(["--origen", str(NUEVOS["csv"]), "--aplicar"]) == 0
    assert config.ARCHIVO_ACTUAL.exists()
    assert ingesta.main(["--listar-versiones"]) == 0
    assert ingesta.main(["--agregar-baja", "55-04000001"]) == 0
    assert ingesta.main(["--restaurar", "original"]) == 0
    assert ingesta.main(["--origen", str(entorno / "no_existe.csv")]) == 1
    assert "No existe" in capsys.readouterr().out
    assert ingesta.main([]) == 2


def test_lectura_por_fsspec_cubre_el_camino_de_la_nube():
    import fsspec

    contenido = NUEVOS["csv"].read_bytes()
    for ruta in ("memory://leads/nuevos.csv", "memory://leads/otro.csv"):
        with fsspec.open(ruta, "wb") as archivo:
            archivo.write(contenido)
        tabla, descripcion = ingesta.leer_fuente(ruta)
        assert len(tabla) == 2 and descripcion == ruta
    with fsspec.open("memory://leads/nuevos.xlsx", "wb") as archivo:
        archivo.write(NUEVOS["xlsx"].read_bytes())
    assert len(ingesta.leer_fuente("memory://leads/nuevos.xlsx")[0]) == 2
    with fsspec.open("memory://leads/nuevos.parquet", "wb") as archivo:
        archivo.write(NUEVOS["parquet"].read_bytes())
    assert len(ingesta.leer_fuente("memory://leads/nuevos.parquet")[0]) == 2


def test_lectura_por_fsspec_de_un_archivo_que_no_existe_da_error_claro():
    with pytest.raises(ingesta.ErrorIngesta, match="No se pudo descargar"):
        ingesta.leer_fuente("memory://leads/no_existe.csv")
