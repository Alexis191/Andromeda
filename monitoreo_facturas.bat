@echo off
echo Iniciando tarea programada de Andromeda...

:: 1. Entrar a la carpeta del proyecto
cd /d C:\inetpub\wwwroot\Andromeda

:: 2. Activar el entorno virtual de Python
call env\Scripts\activate.bat

:: 3. Ejecutar el comando personalizado de Django
python manage.py ejecutar_monitoreo

echo Proceso finalizado.