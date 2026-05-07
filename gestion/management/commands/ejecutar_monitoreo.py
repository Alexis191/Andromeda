from django.core.management.base import BaseCommand
from gestion.tasks import tarea_monitoreo_diario  # Importamos tu tarea original

class Command(BaseCommand):
    help = 'Ejecuta la tarea de monitoreo diario de facturas y caducidades'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando tarea de monitoreo en segundo plano...')
        
        try:
            # Ejecutamos la función original de tu proyecto
            tarea_monitoreo_diario()
            self.stdout.write(self.style.SUCCESS('Monitoreo ejecutado correctamente.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al ejecutar el monitoreo: {e}'))