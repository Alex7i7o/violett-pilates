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
from backend_core.plugin_loader import get_plugin_config
from core.services import generar_turnos_desde_plantillas
from plugins.automatizaciones.backend.management.commands.cancel_empty_classes import Command as CancelEmptyClassesCommand

logger = logging.getLogger(__name__)

@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

def job_cancel_empty_classes():
    cmd = CancelEmptyClassesCommand()
    cmd.handle()

class Command(BaseCommand):
    help = "Inicia el APScheduler leyendo la configuracion de automatizaciones."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        config = get_plugin_config('automatizaciones')
        
        # Cancelar clases vacias
        cancel_rules = config.get('cancel_empty_classes', {})
        if cancel_rules.get('enabled', False):
            scheduler.add_job(
                job_cancel_empty_classes,
                trigger=CronTrigger(minute="*"), # O leer schedule del config
                id="cancel_empty_classes",
                max_instances=1,
                replace_existing=True,
            )
            logger.info("Added job 'cancel_empty_classes'.")

        # Generar plantillas
        generate_rules = config.get('generate_templates', {})
        if generate_rules.get('enabled', False):
            scheduler.add_job(
                generar_turnos_desde_plantillas,
                trigger=CronTrigger(minute="*/2"),
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
