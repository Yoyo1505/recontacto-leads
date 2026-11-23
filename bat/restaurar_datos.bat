@echo off
rem Vuelve a una version anterior de la base. Antes de restaurar se guarda una copia de la
rem version actual, asi que nada se pierde.
rem Uso:  restaurar_datos.bat              muestra las versiones y restaura la mas reciente
rem       restaurar_datos.bat NOMBRE       restaura esa version (ver la lista)
rem       restaurar_datos.bat original     vuelve a la base original
call "%~dp0_entorno.bat" || goto :fin
echo Versiones guardadas:
%PY% -m recontacto.ingesta --listar-versiones
echo.
if "%~1"=="" (
  if /i not "%CONFIRMAR%"=="S" (
    set /p RESPUESTA="Restaurar la version mas reciente? (S/N): "
    if /i not "%RESPUESTA%"=="S" (echo No se cambio nada. & goto :fin)
  )
  %PY% -m recontacto.ingesta --restaurar
) else (
  %PY% -m recontacto.ingesta --restaurar "%~1"
)
:fin
if not "%SIN_PAUSA%"=="1" pause
