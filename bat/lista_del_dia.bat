@echo off
rem Genera la lista del dia sin abrir la aplicacion. Queda en outputs\lista_AAAA-MM-DD.csv
rem Uso: lista_del_dia.bat [AAAA-MM-DD]   (por defecto, el dia siguiente al ultimo registro)
call "%~dp0_entorno.bat" || goto :fin
if "%~1"=="" (
  %PY% -m recontacto.cli
) else (
  %PY% -m recontacto.cli --hoy %~1
)
:fin
if not "%SIN_PAUSA%"=="1" pause
