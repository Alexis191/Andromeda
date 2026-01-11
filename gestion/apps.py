from django.apps import AppConfig
import os

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'

    def ready(self):
        # Evita ejecutar dos veces el scheduler cuando usas runserver con autoreload
        if os.environ.get('RUN_MAIN', None) != 'true':
            from . import updater
            updater.start()