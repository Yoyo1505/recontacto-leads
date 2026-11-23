@echo off
rem Abre el sitio de la entrega (web\sitio\index.html): las cuatro entregas, cada una en su pagina.
rem No instala nada: solo necesita un navegador. Si falta, primero corre construir_web.bat.
cd /d "%~dp0.."
if not exist "%CD%\web\sitio\index.html" (
  echo Falta web\sitio\index.html. Corre bat\construir_web.bat primero.
  pause
  exit /b 1
)
start "" "%CD%\web\sitio\index.html"
