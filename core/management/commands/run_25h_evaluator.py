# Developed by FireSeed - Fueling Innovation
import datetime
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from core.services import evaluar_clases, notificar_profesores_diario, generar_turnos_desde_plantillas

logger = logging.getLogger(__name__)

@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

class Command(BaseCommand):
    help = "Inicia el APScheduler para tareas automáticas (Ej: Evaluador de 25hs)."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Configurado para correr cada minuto (para pruebas locales y asegurar evaluación rápida)
        scheduler.add_job(
            evaluar_clases,
            trigger=CronTrigger(minute="*"),
            id="evaluar_clases",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'evaluar_clases'.")

        scheduler.add_job(
            notificar_profesores_diario,
            trigger=CronTrigger(minute="*/5"),
            id="notificar_profesores",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'notificar_profesores'.")

        scheduler.add_job(
            generar_turnos_desde_plantillas,
            trigger=CronTrigger(minute="*/2"), # En prod sería algo como hour="00", minute="30"
            id="generar_turnos_desde_plantillas",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'generar_turnos_desde_plantillas'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job: 'delete_old_job_executions'.")

        try:
            print("Iniciando motor de automatizaciones (APScheduler)...")
            scheduler.start()
        except KeyboardInterrupt:
            print("Deteniendo APScheduler...")
            scheduler.shutdown()
            print("APScheduler detenido.")
