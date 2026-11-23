@echo off
rem Menu con todo lo que se puede hacer. Doble clic para usarlo.
chcp 65001 >nul
:inicio
cls
echo ==============================================
echo   Recontacto de leads - menu
echo ==============================================
echo   1. Iniciar la aplicacion
echo   2. Generar la lista del dia
echo   3. Ver que pasaria con dos personas nuevas
echo   4. Actualizar datos desde un archivo
echo   5. Actualizar datos desde una base de datos
echo   6. Actualizar datos desde la nube o una web
echo   7. Registrar una baja (no escribirle mas)
echo   8. Volver a una version anterior de los datos
echo   9. Correr las pruebas
echo   A. Instalar librerias
echo   0. Salir
echo.
set "OPCION="
set /p OPCION="Elige una opcion: "
if "%OPCION%"=="1" call "%~dp0iniciar_app.bat"
if "%OPCION%"=="2" call "%~dp0lista_del_dia.bat"
if "%OPCION%"=="3" call "%~dp0simular_dos_personas.bat"
if "%OPCION%"=="4" (set /p RUTA="Ruta del archivo: " & call "%~dp0actualizar_datos.bat" "%RUTA%")
if "%OPCION%"=="5" (set /p TABLA="Nombre de la tabla: " & call "%~dp0actualizar_desde_base.bat" "%TABLA%")
if "%OPCION%"=="6" (set /p URL="Direccion (https://, s3://, gs://, az://): " & call "%~dp0actualizar_desde_nube.bat" "%URL%")
if "%OPCION%"=="7" (set /p TEL="Telefono: " & call "%~dp0registrar_baja.bat" "%TEL%")
if "%OPCION%"=="8" call "%~dp0restaurar_datos.bat"
if "%OPCION%"=="9" call "%~dp0probar.bat"
if /i "%OPCION%"=="A" call "%~dp0instalar.bat"
if "%OPCION%"=="0" exit /b 0
goto :inicio
