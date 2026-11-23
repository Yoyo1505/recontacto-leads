@echo off
rem Corre todas las pruebas automaticas del proyecto.
call "%~dp0_entorno.bat" || goto :fin
%PY% -m pytest -q
:fin
if not "%SIN_PAUSA%"=="1" pause
