@echo off
rem Recalcula las metricas del modelo y las figuras (docs\figuras) con los datos actuales.
call "%~dp0_entorno.bat" || goto :fin
%PY% -m recontacto.cli --evaluar
:fin
if not "%SIN_PAUSA%"=="1" pause
