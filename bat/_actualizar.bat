@echo off
rem Actualiza la base de leads en dos pasos: primero muestra el informe y que haria la
rem herramienta con las personas nuevas; solo guarda si confirmas con S.
rem Se usa desde los otros .bat con: call "%~dp0_actualizar.bat" --origen ...
call "%~dp0_entorno.bat" || goto :fin
echo.
echo === Paso 1: informe (todavia no se guarda nada) ===
%PY% -m recontacto.ingesta %* --simular
if errorlevel 1 goto :fin
echo.
if /i "%CONFIRMAR%"=="S" goto :aplicar
set /p RESPUESTA="Aplicar estos cambios? (S/N): "
if /i not "%RESPUESTA%"=="S" (
  echo No se guardo nada.
  goto :fin
)
:aplicar
echo.
echo === Paso 2: guardando ===
%PY% -m recontacto.ingesta %* --aplicar
if errorlevel 1 goto :fin
echo.
echo Listo. Para volver a la version anterior usa restaurar_datos.bat
:fin
if not "%SIN_PAUSA%"=="1" pause
