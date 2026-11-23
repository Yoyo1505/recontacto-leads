@echo off
rem Instala las librerias del proyecto (una sola vez).
call "%~dp0_entorno.bat" || goto :fin
echo Instalando librerias del proyecto...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo Hubo un problema con la instalacion. & goto :fin)
echo.
echo Listo. Siguiente paso: iniciar_app.bat
:fin
if not "%SIN_PAUSA%"=="1" pause
