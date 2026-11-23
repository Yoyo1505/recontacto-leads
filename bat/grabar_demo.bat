@echo off
rem Regraba el GIF de la presentacion (docs\demo\demo.gif). La aplicacion debe estar corriendo
rem (iniciar_app.bat en otra ventana) y Chrome instalado.
call "%~dp0_entorno.bat" || goto :fin
%PY% scripts\grabar_demo.py
:fin
if not "%SIN_PAUSA%"=="1" pause
