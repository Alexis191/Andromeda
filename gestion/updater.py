# gestion/updater.py
from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import tarea_monitoreo_diario

def start():
    scheduler = BackgroundScheduler()
    # Ejecutar todos los días a las 8:00 AM
    scheduler.add_job(tarea_monitoreo_diario, 'cron', hour=8, minute=0)
    scheduler.start()