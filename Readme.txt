0. Instalar visual studio code.
0. Instalar sql server.
0. Instalar ODBC Driver 17 for SQL Server
    Acceder a: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17
0. Instalar python en la computadora:
    Acceder a: https://www.python.org/downloads/
1. Crear una carpeta para el nuevo proyecto:
    Dentro de la carpeta abrir un terminal y ejecutar: code .
2. Dentro de VSC abrir un terminal y crear un entorno virtual:
    Ejecutar: python -m venv env
3. Activar el estorno virtual:
    Ejecutar: .\env\Scripts\activate
4. Ver que paquetes tenemos instalado por defecto: 
    Ejecutar: pip list
    Resultado: pip 25.2
5. Intalar librerías necesarias: 
	Ejecutar: pip install django mssql-django pyodbc apscheduler openpyxl
6. Comprobar los paquetes que necesitamos:
    Ejecutar: pip list
    Resultado: 
        APScheduler  3.11.2
        asgiref      3.11.0
        Django       5.2.9
        et_xmlfile   2.0.0
        mssql-django 1.6
        openpyxl     3.1.5
        pip          25.2
        pyodbc       5.3.0
        pytz         2025.2
        sqlparse     0.5.5
        tzdata       2025.3
        tzlocal      5.3.1
7. Crear un proyecto de Django:
    Ejecutar: django-admin startproject menatics .
    Resultado: Se crea una carpeta menatics con todos los archivos py necesarios
8. Configurar en el archivo settings.py la base de datos:
    'default': {
            'ENGINE': 'mssql', #sql_server.pyodbc
            'NAME': 'Andromeda',
            'USER': 'sa',           # <-- Cambia esto por tu usuario de SQL Server
            'PASSWORD': '1q2w3eMenatics',    # <-- Cambia esto por tu contraseña de SQL Server
            'HOST': 'ALEXIS\INFORMATICS',              # O la IP de tu servidor SQL (ej. '127.0.0.1')
            'PORT': '',                       # Usualmente vacío, o '1433' si tienes un puerto específico
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server', # O la versión de tu driver, si es diferente
            },
        }
8. Realizar la migracion a la base de datos para comprobar si esta bien configurada la BDD
    Ejecutar: python manage.py migrate
    Resultado: OK
13. Crear una aplicación llamada gestion
    Ejecutar: python manage.py startapp gestion

PARA EJECUTAR EL PROGRAMA: python manage.py runserver
SUPERADMINISTRADOR
User: alexisntn@hotmail.com
Pass: 1q2w3eMenatics

USUARIO
User: admin@gmail.com
Pass: 123