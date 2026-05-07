Sistema de Gestión y Alertas Automáticas - Proyecto Andrómeda
Este proyecto es una solución tecnológica desarrollada para la Corporación Menatics Cía. Ltda., diseñada para automatizar el seguimiento, control y notificación de vencimientos de servicios de facturación electrónica. El sistema optimiza la gestión operativa mediante alertas automáticas, monitoreo de consumo en tiempo real y reportes de inteligencia de negocios.
🚀 Características Principales
	Gestión de Clientes: CRUD completo para la administración de datos comerciales y técnicos.
	Automatización de Alertas: Envío automático de correos electrónicos preventivos sobre vencimientos de planes (job programado a las 08:00 AM).
	Monitoreo de Consumo: Verificación en tiempo real del consumo de facturas y alertas de umbral (80% y 90%).
	Importación Masiva: Carga de clientes mediante archivos Excel (.xlsx) con validación de datos.
	Reportes: Generación de reportes de ventas, renovaciones y deserciones exportables a Excel.
	Dashboard Interactivo: Calendario de vencimientos por colores y métricas clave.
🛠️ Tecnologías Utilizadas
	Backend: Python 3.14, Django 5.2.9
	Base de Datos: Microsoft SQL Server
	Automatización: APScheduler
	Manejo de Archivos: Openpyxl
	Conexión BD: mssql-django, pyodbc
📋 Requisitos Previos
Antes de instalar el proyecto, asegúrate de tener instalado lo siguiente en tu sistema:
	Python 3.113: Descargar Python en: https://www.python.org/downloads/
	Microsoft SQL Server: Tener una instancia local o remota activa.
	ODBC Driver 17 for SQL Server: Necesario para la conexión entre Django y SQL Server.Descargar ODBC Driver 17 en: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17
	Visual Studio Code (Recomendado).
🔧 Instalación y Configuración
Sigue estos pasos para ejecutar el proyecto en tu entorno local:
1. Clonar el repositorio y preparar el entorno
Abre una terminal en la carpeta del proyecto y ejecuta los siguientes comandos:
# Crear entorno virtual
python -m venv env
# Activar entorno virtual (Windows)
.\env\Scripts\activate

# Instalar dependencias
pip install django mssql-django pyodbc apscheduler openpyxl

2. Configuración de la Base de DatosDebes configurar tus credenciales de SQL Server en el archivo menatics/settings.py. Busca la sección DATABASES y ajústala según tu configuración local:PythonDATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'Andromeda',            # Nombre de la BDD
        'USER': 'sa',                   # Tu usuario de SQL Server
        'PASSWORD': 'TuContraseñaAqui', # Tu contraseña de SQL Server
        'HOST': 'ALEXIS\INFORMATICS',   # Tu servidor o IP (ej. localhost)
        'PORT': '',                     # Generalmente vacío o 1433
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

3. Migraciones e Inicialización
Una vez configurada la base de datos, ejecuta las migraciones para crear las tablas necesarias:
python manage.py migrate
(Si el comando finaliza con "OK", la conexión a la base de datos es correcta).

▶️ Ejecución del Proyecto
Para iniciar el servidor de desarrollo:
python manage.py runserver
Accede al navegador en: http://127.0.0.1:8000/
🔐 Credenciales de Acceso (Entorno de Pruebas)
El sistema cuenta con roles diferenciados. Puedes utilizar las siguientes credenciales preconfiguradas para pruebas:
SUPERADMINISTRADOR
User: alexisntn@hotmail.com
Pass: 1q2w3eMenatics

USUARIO
User: admin@gmail.com
Pass: 123
Nota de Seguridad: Se recomienda cambiar estas contraseñas inmediatamente si se va a desplegar el sistema en un entorno productivo.

👥 Autores
Alexis Xavier Collaguazo Andrango - Desarrollo e Implementación
Universidad Politécnica Salesiana - Carrera de Negocios Digitales