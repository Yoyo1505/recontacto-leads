@echo off
rem Regenera la version web: exporta datos y modelo desde Python, arma la pagina y comprueba que
rem JavaScript da lo mismo que Python. Requiere Node.js para la comprobacion.
call "%~dp0_entorno.bat" || goto :fin
%PY% scripts\exportar_web.py
if errorlevel 1 goto :fin
%PY% scripts\construir_web.py
if errorlevel 1 goto :fin
node web\prueba_motor.js
:fin
if not "%SIN_PAUSA%"=="1" pause
