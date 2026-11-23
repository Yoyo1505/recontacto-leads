@echo off
rem Abre el sitio de la entrega (web\sitio\herramienta.html). Las otras entregas se abren desde su menu.
rem No instala nada: solo necesita un navegador. Si falta, primero corre construir_web.bat.
cd /d "%~dp0.."
if not exist "%CD%\web\sitio\herramienta.html" (
  echo Falta web\sitio\herramienta.html. Corre bat\construir_web.bat primero.
  pause
  exit /b 1
)
start "" "%CD%\web\sitio\herramienta.html"
