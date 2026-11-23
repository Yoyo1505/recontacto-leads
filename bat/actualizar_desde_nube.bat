@echo off
rem Actualiza la base desde un archivo en la nube o en una direccion web.
rem Direcciones aceptadas: https://..., s3://bucket/archivo.csv, gs://bucket/archivo.parquet,
rem az://contenedor/archivo.xlsx (para s3, gs y az instala antes la libreria con
rem instalar_nube_y_bases.bat).
rem Las credenciales van en variables de entorno del servicio (por ejemplo AWS_ACCESS_KEY_ID y
rem AWS_SECRET_ACCESS_KEY), NUNCA dentro de la direccion ni de este archivo.
rem Uso:  actualizar_desde_nube.bat s3://mi-bucket/leads/nuevos.csv
rem       (o define RECONTACTO_NUBE_URL y ejecuta sin argumentos)
if "%~1"=="" (
  if "%RECONTACTO_NUBE_URL%"=="" (
    echo Indica la direccion. Ejemplo: actualizar_desde_nube.bat s3://mi-bucket/nuevos.csv
    if not "%SIN_PAUSA%"=="1" pause
    exit /b 2
  )
  call "%~dp0_actualizar.bat" --origen env:RECONTACTO_NUBE_URL
) else (
  call "%~dp0_actualizar.bat" --origen "%~1"
)
