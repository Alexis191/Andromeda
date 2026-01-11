from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3xjen7-*j#k!hlwclu0x$7r!)y_hg2b1l6j9vmyc_y77c-t=um'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'menatics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'menatics.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'mssql', #sql_server.pyodbc
        'NAME': 'Andromeda',
        'USER': 'sa',           # <-- Cambia esto por tu usuario de SQL Server
        'PASSWORD': '1q2w3eMenatics',    # <-- Cambia esto por tu contraseña de SQL Server
        'HOST': '192.168.1.46',              # O la IP de tu servidor SQL (ej. '127.0.0.1')
        'PORT': '1433',                       # Usualmente vacío, o '1433' si tienes un puerto específico
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server', # O la versión de tu driver, si es diferente
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración para usar Email en el Login
AUTHENTICATION_BACKENDS = [
    'menatics.authentication.EmailBackend',  # El archivo que acabamos de crear
    'django.contrib.auth.backends.ModelBackend', # Respaldo (para el admin por defecto)
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login' 

# Cierra la sesión automáticamente al cerrar el navegador
#SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# menatics/settings.py

# Configuración de Correo (Ejemplo para Gmail, cambia según tu proveedor)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com' # O tu servidor SMTP corporativo (ej: outlook.office365.com)
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'collaguazoalexis99@gmail.com'
EMAIL_HOST_PASSWORD = 'btag wfns bbcj ljmk' # Usa App Password si es Gmail/Outlook
DEFAULT_FROM_EMAIL = 'Sistema Andrómeda <collaguazoalexis99@gmail.com>'

# Correo del personal operativo que recibirá las alertas
OPERATIONS_EMAIL = 'alexisntn@hotmail.com'
