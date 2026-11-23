"""Ingesta de datos: leer, validar, fusionar y versionar la base de leads.

Flujo (cada paso es una funcion)
    leer_fuente / leer_bytes   CSV, JSON, Excel, Parquet, SQLite, bases SQL (SQLAlchemy) y URLs
                               (http, https, s3, gs, az) -> tabla cruda
    normalizar_columnas        acepta sinonimos de columnas y avisa de las que faltan o sobran
    validar                    revisa fila por fila; lo rechazado queda con su motivo, nada se pierde
    fusionar                   agrega leads nuevos y actualiza los existentes por `lead_id`; nunca borra
    guardar_version            guarda la base nueva y una copia de la anterior (se puede restaurar)

Modulos del paquete
    esquema (columnas, sinonimos, errores, informe) · utilidades · lectura · validacion · fusion
    versiones (guardar, restaurar, bajas) · simulacion · cli. Este archivo reexporta todo.

Cuidado con las personas
    - Un archivo mal formado no cambia nada: primero se muestra el informe y solo se aplica si se pide.
    - Los telefonos que pidieron no recibir mensajes se guardan en `data/bajas.csv` (`agregar_baja`) y
      se respetan siempre, venga el dato de donde venga.
    - Las contrasenas de las cadenas de conexion no se escriben en pantalla, bitacoras ni archivos.

Donde cambiar cosas
    - Columnas obligatorias y sinonimos: `REQUERIDAS` y `SINONIMOS`.
    - Valores validos de `resultado`: `RESULTADOS` y `SINONIMOS_RESULTADO`.
    - Reglas de validacion por fila: funcion `validar`.
    - Cuantas versiones se conservan: `config.VERSIONES_A_CONSERVAR`.

Uso desde la linea de comandos
    python -m recontacto.ingesta --origen nuevos.xlsx                 informe (no cambia nada)
    python -m recontacto.ingesta --origen nuevos.xlsx --simular        que pasaria con esas personas
    python -m recontacto.ingesta --origen nuevos.xlsx --aplicar        guarda los cambios
    python -m recontacto.ingesta --origen env:RECONTACTO_DB_URL --tabla leads --aplicar
    python -m recontacto.ingesta --listar-versiones | --restaurar [nombre|original]
    python -m recontacto.ingesta --agregar-baja 5512345678
"""

from .cli import _parser, main
from .esquema import (
    CANALES_CONOCIDOS,
    COLUMNAS,
    ESQUEMAS_BASE_DE_DATOS,
    FORMATOS_FECHA,
    LIMITE_BYTES,
    OPCIONALES,
    REQUERIDAS,
    RESULTADOS,
    SEGUIMIENTO,
    SINONIMOS,
    SINONIMOS_RESULTADO,
    SQL_PROHIBIDO,
    ErrorIngesta,
    Informe,
)
from .fusion import fusionar, leer_canonico, procesar
from .lectura import _leer_base_de_datos, leer_bytes, leer_fuente
from .simulacion import decisiones_para, simular_llegada
from .utilidades import _clave_columna, _extension, _fecha, _igual, _numero, _resultado, _texto, enmascarar
from .validacion import normalizar_columnas, validar
from .versiones import _formatear_para_guardar, agregar_baja, aplicar, guardar_version, listar_versiones, restaurar
