@echo off
rem Prepara el entorno para los demas .bat: carpeta del proyecto, rutas y Python.
rem No se ejecuta solo; lo llaman los otros archivos con: call "%~dp0_entorno.bat"
chcp 65001 >nul
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  echo No se encontro Python. Instala Python 3.11 o superior desde https://www.python.org y vuelve a intentar.
  exit /b 1
)
exit /b 0
