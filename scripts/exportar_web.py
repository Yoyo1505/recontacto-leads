"""Exporta datos, modelos y resultados de referencia para la version web (web/*.json).

La version web reimplementa en JavaScript la logica de recontacto para que la herramienta abra en el
navegador sin instalar nada. Este script calcula con la version en Python lo que la web necesita:

    datos.json        leads originales, compactos
    modelo.json       modelo logistico principal y modelos bootstrap (coeficientes)
    evidencia.json    series ya calculadas para las graficas de evidencia
    referencia.json   lista del dia calculada en Python, para comprobar que JavaScript da lo mismo

Uso:  set PYTHONPATH=src  y  python scripts/exportar_web.py
"""

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from recontacto import config, control, evaluation, features, mensajes, pipeline, respuestas  # noqa: E402
from recontacto import simulacion as sim  # noqa: E402
from recontacto.data import cargar_leads  # noqa: E402
from recontacto.model import ModeloContacto  # noqa: E402

SALIDA = RAIZ / "web"
CASOS_EXTRA = [
    "no", "STOP", "Dejen de escribirme", "no me escriban más", "Ya no me interesa", "sí", "Claro que sí", "Me interesa", "ok",
    "a las 5 pm", "a las 5 p.m.", "hoy en la tarde", "16:00", "no puedo hoy", "no puedo hoy pero mañana a las 4", "más tarde",
    "¿Qué incluye?", "Buenas tardes, ¿me pueden llamar a las 6?", "¿Cuánto cuesta? llámame a las 4", "pasado mañana a las 9 am",
    "tengo una emergencia", "jajaja", "", "mañana", "en la tarde", "sí, ¿qué incluye?", "a las 10:30",
]
CATEGORICAS = features.CATEGORICAS
NUMERICAS = features.NUMERICAS


def numero(valor):
    return None if valor is None or (isinstance(valor, float) and np.isnan(valor)) else float(valor)


def exportar_modelo(modelo, categorias_globales):
    pre = modelo.pipeline.named_steps["pre"]
    clf = modelo.pipeline.named_steps["clf"]
    coef = clf.coef_[0]
    nombres = list(pre.get_feature_names_out())
    por_nombre = dict(zip(nombres, coef))
    media = dict(zip(nombres, modelo.media_))
    codificador = pre.named_transformers_["cat"]
    salida = {"intercepto": float(clf.intercept_[0]), "cat": {}, "media_cat": {}, "num": {}}
    for columna, categorias in zip(CATEGORICAS, codificador.categories_):
        presentes = {str(c) for c in categorias}
        salida["cat"][columna] = {
            c: (float(por_nombre[f"cat__{columna}_{c}"]) if c in presentes else 0.0) for c in categorias_globales[columna]
        }
        salida["media_cat"][columna] = {
            c: (float(media[f"cat__{columna}_{c}"]) if c in presentes else 0.0) for c in categorias_globales[columna]
        }
    imputador_escalador = pre.named_transformers_["num"]
    mediana = imputador_escalador.named_steps["imp"].statistics_
    escalador = imputador_escalador.named_steps["esc"]
    for i, columna in enumerate(NUMERICAS):
        salida["num"][columna] = {
            "mediana": float(mediana[i]),
            "media": float(escalador.mean_[i]),
            "escala": float(escalador.scale_[i]),
            "coef": float(por_nombre[f"num__{columna}"]),
            "media_x": float(media[f"num__{columna}"]),
        }
    return salida


def guardar(nombre, objeto):
    (SALIDA / f"{nombre}.json").write_text(
        json.dumps(objeto, ensure_ascii=False, separators=(",", ":"), default=float), encoding="utf-8"
    )


def main():
    SALIDA.mkdir(exist_ok=True)
    df = cargar_leads(config.ARCHIVO_ORIGINAL)
    X, y = features.desde_contactos(df)

    columnas = [
        "lead_id", "fecha_registro", "canal", "anuncio", "estado", "edad", "objetivo",
        "plan_de_interes", "telefono", "asesor", "primer_contacto", "resultado", "monto_venta",
    ]
    filas = []
    for _, f in df.sort_values("lead_id").iterrows():
        filas.append(
            [
                f["lead_id"],
                f["fecha_registro"].strftime("%Y-%m-%d %H:%M"),
                f["canal"],
                None if pd.isna(f["anuncio"]) else f["anuncio"],
                f["entidad"],
                numero(f["edad"]),
                f["objetivo"],
                numero(f["plan_de_interes"]),
                f["telefono"],
                None if pd.isna(f["asesor"]) else f["asesor"],
                None if pd.isna(f["primer_contacto"]) else f["primer_contacto"].strftime("%Y-%m-%d %H:%M"),
                f["resultado"],
                numero(f["monto_venta"]),
            ]
        )
    guardar("datos", {"columnas": columnas, "filas": filas})

    principal = ModeloContacto("logistica").entrenar(X, y)
    categorias = {
        columna: [str(c) for c in cats]
        for columna, cats in zip(CATEGORICAS, principal.pipeline.named_steps["pre"].named_transformers_["cat"].categories_)
    }
    bootstrap = sim.modelos_bootstrap(X, y, n=100)
    conversion = sim.tasa_venta_por_canal(df)
    guardar(
        "modelo",
        {
            "categorias": categorias,
            "principal": exportar_modelo(principal, categorias),
            "bootstrap": [exportar_modelo(m, categorias) for m in bootstrap],
            "conversion": {k: float(v) for k, v in conversion.items()},
            "espera_referencia_h": config.ESPERA_REFERENCIA_H,
        },
    )

    resultados = evaluation.evaluar_modelos(df)[0]
    unicos = df[~df["es_duplicado"]]
    evidencia = {
        "tasa_contesta": float(y.mean()),
        "leads_por_dia": float(unicos.groupby(unicos["fecha_registro"].dt.normalize()).size().mean()),
        "tasas": {},
    }
    for columna in ("franja_hora", "rango_espera", "canal", "dia_semana"):
        t = control.tasas_por(X, y, columna)
        evidencia["tasas"][columna] = t.rename(columns={columna: "categoria"}).to_dict("records")
    franjas, esperas = features._FRANJAS, features._ESPERAS
    evidencia["confusion"] = {"franjas": franjas, "esperas": esperas, "z": [], "n": []}
    tabla = X.assign(no_contesta=1 - y.to_numpy())
    for f in franjas:
        fila_z, fila_n = [], []
        for e in esperas:
            celda = tabla[(tabla["franja_hora"] == f) & (tabla["rango_espera"] == e)]
            fila_n.append(int(len(celda)))
            fila_z.append(float(celda["no_contesta"].mean() * 100) if len(celda) >= 10 else None)
        evidencia["confusion"]["z"].append(fila_z)
        evidencia["confusion"]["n"].append(fila_n)
    evidencia["ablacion"] = resultados["ablacion"]
    evidencia["metricas"] = {k: resultados[k] for k in ("corte", "n_entrenamiento", "n_prueba", "constante", "logistica", "arbol")}
    evidencia["calibracion"] = resultados["calibracion_logistica"]
    carta = control.carta_p(df)
    evidencia["carta_p"] = [
        {
            "fecha": r["fecha"].strftime("%Y-%m-%d"),
            "n": int(r["n"]),
            "tasa": float(r["tasa"]),
            "centro": float(r["centro"]),
            "alto": float(r["limite_alto"]),
            "bajo": float(r["limite_bajo"]),
            "fuera": bool(r["fuera_de_control"]),
        }
        for _, r in carta.iterrows()
    ]
    g, limites, centro = control.embudo(df)
    evidencia["embudo_asesores"] = {"asesores": g.to_dict("records"), "centro": centro, "limites": limites.to_dict("list")}
    contactados = unicos[unicos["primer_contacto"].notna()]
    contestaron = contactados[contactados["resultado"] != "no_contesta"]
    evidencia["embudo"] = {
        "etapas": ["Pidieron información", "Recibieron un contacto", "Contestaron", "Compraron"],
        "valores": [
            int(len(unicos)),
            int(len(contactados)),
            int(len(contestaron)),
            int((contestaron["resultado"] == "venta").sum()),
        ],
    }
    evidencia["no_contesta_canal"] = control.tabla_con_intervalos(df, "canal").to_dict("records")
    guardar("evidencia", evidencia)

    ahora = datetime(2026, 11, 9, 8, 0)
    lista, excluidos = pipeline.generar_lista(df, principal, ahora, config.REGLAS)
    p0 = float(y.mean())
    referencia = {
        "ahora": "2026-11-09 08:00",
        "lista": [
            {
                "lead_id": r["lead_id"],
                "prioridad": int(r["prioridad"]),
                "accion": r["accion"],
                "intento": int(r["intento"]),
                "horario": None if pd.isna(r["horario_asignado"]) else r["horario_asignado"].strftime("%Y-%m-%d %H:%M"),
                "prob": None if pd.isna(r["prob_asignada"]) else float(r["prob_asignada"]),
                "prob_promedio": float(r["prob_promedio"]),
                "motivo": r["motivo"],
                "mensaje": r["mensaje"],
                "etapa": r["etapa"],
                "variante": r["variante"],
            }
            for _, r in lista.iterrows()
        ],
        "excluidos": excluidos["motivo_exclusion"].value_counts().to_dict(),
        "ab": {
            "p0": p0,
            "n_3pts": sim.tamano_muestra(p0, 0.03),
            "n_8pts": sim.tamano_muestra(p0, 0.08),
            "potencia_3pts_1000": sim.potencia_analitica(p0, 0.03, 1000),
        },
    }
    elegibles, marco, asignados, _ = pipeline.calcular_asignacion(df, principal, ahora, config.REGLAS)
    prep = sim.preparar(elegibles, marco, asignados, bootstrap)
    referencia["simulacion"] = {
        "n_leads": prep.n_leads,
        "p_politica_media": float(prep.p_politica.mean()),
        "p_base_media": float(prep.p_base.mean()),
        "resumen": {str(a): sim.resumen(sim.simular(prep, a, 4000, conversion=conversion)) for a in (0.0, 0.5, 1.0)},
    }
    guardar("referencia", referencia)

    casos = list(respuestas.EJEMPLOS) + CASOS_EXTRA
    guardar(
        "casos_respuestas",
        [{"texto": t, **{k: v for k, v in asdict(respuestas.clasificar(t)).items()}} for t in casos],
    )
    contextos = []
    for etapa, variantes in mensajes.BIBLIOTECA.items():
        for letra in sorted(variantes):
            for ia, dias in ((False, 0), (True, 4)):
                contexto = {"nunca_contactado": etapa == "primer_contacto", "ultimo_intento": etapa == "cierre", "variante": letra, "franja_dia": "el martes por la tarde", "asesor": "Asesor B", "origen_ia": ia, "dias": dias}
                contextos.append({"nunca": contexto["nunca_contactado"], "ultimo": contexto["ultimo_intento"], "variante": letra, "franja": contexto["franja_dia"], "asesor": "Asesor B", "origenIa": ia, "dias": dias, "texto": mensajes.plantilla(contexto)})
    guardar("casos_mensajes", {"plantillas": contextos, "crc": [{"lead": f"L{i:05d}", "etapa": e, "variante": mensajes.elegir_variante(f"L{i:05d}", e)} for i in (1, 17, 123, 999, 1800) for e in mensajes.BIBLIOTECA]})
    for nombre in ("datos", "modelo", "evidencia", "referencia"):
        print(nombre, round((SALIDA / f"{nombre}.json").stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
