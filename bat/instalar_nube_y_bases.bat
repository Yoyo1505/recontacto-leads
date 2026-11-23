@echo off
rem Instala librerias OPCIONALES para leer de la nube o de bases de datos.
rem Elige solo la que necesitas. Las contrasenas y llaves NUNCA van en estos archivos:
rem se definen como variables de entorno (ver docs\README.md, seccion Datos).
call "%~dp0_entorno.bat" || goto :fin
echo Que quieres instalar?
echo   1. Amazon S3            (s3fs)
echo   2. Google Cloud Storage (gcsfs)
echo   3. Azure Blob Storage   (adlfs)
echo   4. PostgreSQL           (psycopg2-binary)
echo   5. MySQL / MariaDB      (pymysql)
echo   6. SQL Server           (pyodbc)
echo   0. Salir
set /p OPCION="Opcion: "
set "PAQUETE="
if "%OPCION%"=="1" set "PAQUETE=s3fs"
if "%OPCION%"=="2" set "PAQUETE=gcsfs"
if "%OPCION%"=="3" set "PAQUETE=adlfs"
if "%OPCION%"=="4" set "PAQUETE=psycopg2-binary"
if "%OPCION%"=="5" set "PAQUETE=pymysql"
if "%OPCION%"=="6" set "PAQUETE=pyodbc"
if not defined PAQUETE (echo No se instalo nada. & goto :fin)
%PY% -m pip install %PAQUETE%
:fin
if not "%SIN_PAUSA%"=="1" pause
