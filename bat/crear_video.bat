@echo off
rem Crea el video MP4 de la presentacion (docs\demo\demo.mp4): recorrido por la aplicacion y
rem conversaciones de ejemplo (ilustrativas). La aplicacion debe estar corriendo (iniciar_app.bat
rem en otra ventana) y Chrome instalado. Tarda unos 4 minutos.
call "%~dp0_entorno.bat" || goto :fin
%PY% scripts\crear_video.py
:fin
if not "%SIN_PAUSA%"=="1" pause
