import argparse
import json
from datetime import datetime

from . import config, evaluation, features, llm, pipeline
from .data import cargar_leads, fecha_sugerida, leer_bajas
from .model import ModeloContacto


def entrenar_modelo(df):
    X, y = features.desde_contactos(df)
    return ModeloContacto("logistica").entrenar(X, y)


def construir_parser():
    parser = argparse.ArgumentParser(description="Lista diaria de recontacto de leads")
    parser.add_argument("--hoy", default=None, help="AAAA-MM-DD; por defecto, el dia siguiente al ultimo registro")
    base = config.REGLAS
    parser.add_argument("--capacidad-hora", type=int, default=base.capacidad_por_hora)
    parser.add_argument("--max-intentos", type=int, default=base.max_intentos)
    parser.add_argument("--hora-inicio", type=int, default=base.hora_inicio)
    parser.add_argument("--hora-fin", type=int, default=base.hora_fin)
    parser.add_argument("--ventana-dias", type=int, default=base.ventana_dias)
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--evaluar", action="store_true")
    return parser


def main(argumentos=None):
    args = construir_parser().parse_args(argumentos)
    df = cargar_leads(config.ruta_datos_activa(), leer_bajas(config.ARCHIVO_BAJAS))
    ahora = datetime.strptime(args.hoy, "%Y-%m-%d").replace(hour=8) if args.hoy else fecha_sugerida(df)
    args.hoy = ahora.strftime("%Y-%m-%d")
    config.SALIDAS.mkdir(exist_ok=True)

    if args.evaluar:
        resultados, _, _ = evaluation.evaluar_modelos(df)
        config.FIGURAS.mkdir(parents=True, exist_ok=True)
        evaluation.graficar(
            df,
            resultados,
            config.FIGURAS / "exploracion.png",
            config.FIGURAS / "calibracion.png",
        )
        with open(config.SALIDAS / "evaluacion.json", "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, ensure_ascii=False, indent=2)
        print(json.dumps({k: v for k, v in resultados.items() if k != "calibracion_logistica"}, indent=2))

    cliente = None
    if args.llm:
        cliente = llm.ClienteAnthropic()
        if not cliente.disponible:
            print("ANTHROPIC_API_KEY no está definida: se usarán las plantillas.")
            cliente = None

    modelo = entrenar_modelo(df)
    reglas = config.Reglas(
        hora_inicio=args.hora_inicio,
        hora_fin=args.hora_fin,
        max_intentos=args.max_intentos,
        ventana_dias=args.ventana_dias,
        capacidad_por_hora=args.capacidad_hora,
    )
    lista, excluidos = pipeline.generar_lista(df, modelo, ahora, reglas, cliente)
    ruta = config.SALIDAS / f"lista_{args.hoy}.csv"
    lista.to_csv(ruta, index=False, encoding="utf-8-sig")

    print(f"Leads en la lista: {len(lista)} (contactar: {(lista['accion'] == 'contactar').sum()}, en cola: {(lista['accion'] == 'en_cola').sum()})")
    print("Excluidos por regla:")
    print(excluidos["motivo"].value_counts().to_string())
    print(f"Archivo: {ruta}")


if __name__ == "__main__":
    main()
