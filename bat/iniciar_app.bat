@echo off
rem Inicia la aplicacion Dash y la abre en el navegador.
rem Uso: iniciar_app.bat [puerto]     (por defecto 8050)
call "%~dp0_entorno.bat" || goto :fin
set "PUERTO=%~1"
if "%PUERTO%"=="" set "PUERTO=8050"
echo Iniciando la aplicacion en http://127.0.0.1:%PUERTO%  (Ctrl+C para detenerla)
start "" "http://127.0.0.1:%PUERTO%"
%PY% app\dash_app.py --puerto %PUERTO%
:fin
if not "%SIN_PAUSA%"=="1" pause
