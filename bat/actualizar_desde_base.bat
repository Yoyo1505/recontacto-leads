@echo off
rem Actualiza la base desde una base de datos SQL (SQLite, PostgreSQL, MySQL, SQL Server...).
rem La cadena de conexion se toma de la variable de entorno RECONTACTO_DB_URL, para que la
rem contrasena no quede escrita en este archivo ni en el historial de comandos. Ejemplos:
rem    setx RECONTACTO_DB_URL "sqlite:///C:/datos/leads.db"
rem    setx RECONTACTO_DB_URL "postgresql://usuario:clave@servidor:5432/clivi"
rem (cierra y vuelve a abrir la ventana despues de usar setx).
rem Usa un usuario de la base con permiso SOLO de lectura.
rem Uso:  actualizar_desde_base.bat nombre_de_tabla
rem       actualizar_desde_base.bat --consulta "SELECT * FROM leads WHERE fecha_registro >= '2026-11-01'"
if "%RECONTACTO_DB_URL%"=="" (
  echo Falta la variable RECONTACTO_DB_URL con la cadena de conexion. Ver instrucciones en este archivo.
  if not "%SIN_PAUSA%"=="1" pause
  exit /b 2
)
if "%~1"=="" (
  echo Indica la tabla o --consulta. Ejemplo: actualizar_desde_base.bat leads
  if not "%SIN_PAUSA%"=="1" pause
  exit /b 2
)
if /i "%~1"=="--consulta" (
  call "%~dp0_actualizar.bat" --origen env:RECONTACTO_DB_URL --consulta "%~2"
) else (
  call "%~dp0_actualizar.bat" --origen env:RECONTACTO_DB_URL --tabla "%~1"
)
