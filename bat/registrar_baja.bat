@echo off
rem Registra a una persona que pidio no recibir mas mensajes. Desde ese momento no aparece en
rem ninguna lista, aunque su telefono vuelva a llegar en archivos futuros (data\bajas.csv).
rem Uso:  registrar_baja.bat 55-12345678
call "%~dp0_entorno.bat" || goto :fin
if "%~1"=="" (
  echo Indica el telefono. Ejemplo: registrar_baja.bat 55-12345678
  goto :fin
)
%PY% -m recontacto.ingesta --agregar-baja "%~1"
:fin
if not "%SIN_PAUSA%"=="1" pause
