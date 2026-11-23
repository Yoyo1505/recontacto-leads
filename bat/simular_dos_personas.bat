@echo off
rem Muestra que haria la herramienta si llegan dos personas nuevas: una que nunca ha sido
rem contactada (llegada por un agente de IA) y otra que no contesto un primer intento.
rem No guarda nada: es solo una demostracion con data\ejemplos\dos_personas_nuevas.csv.
rem Uso:  simular_dos_personas.bat [otro_archivo]
call "%~dp0_entorno.bat" || goto :fin
set "ARCHIVO=%~1"
if "%ARCHIVO%"=="" set "ARCHIVO=data\ejemplos\dos_personas_nuevas.csv"
%PY% -m recontacto.ingesta --origen "%ARCHIVO%" --simular
:fin
if not "%SIN_PAUSA%"=="1" pause
