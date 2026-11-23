@echo off
rem Actualiza la base desde un archivo: CSV, JSON, Excel (.xlsx), Parquet o SQLite (.db).
rem Primero muestra el informe y que haria la herramienta con las personas nuevas;
rem solo guarda si confirmas. Cada cambio guarda una copia de la version anterior.
rem Uso:  actualizar_datos.bat ruta\al\archivo.xlsx [hoja]
rem       (o arrastra el archivo encima de este .bat)
if "%~1"=="" (
  echo Indica el archivo. Ejemplo: actualizar_datos.bat C:\datos\nuevos.xlsx
  echo Formatos: csv, json, jsonl, xlsx, parquet, sqlite.
  if not "%SIN_PAUSA%"=="1" pause
  exit /b 2
)
if "%~2"=="" (
  call "%~dp0_actualizar.bat" --origen "%~1"
) else (
  call "%~dp0_actualizar.bat" --origen "%~1" --hoja "%~2"
)
