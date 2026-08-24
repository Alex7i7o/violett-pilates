import logging
from django.conf import settings
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from django.utils import timezone
import datetime

from core.models import Turno, Reserva, Usuario
from core.whatsapp_service import notificar_cancelacion_clase, notificar_alerta_cupo, notificar_recordatorio_asistencia

logger = logging.getLogger(__name__)

def evaluar_clases():
    """
    Evalúa los turnos que están exactamente a <= 25 horas y > 24 horas de distancia,
    y que no hayan sido evaluados aún.
    """
    now = timezone.now()
    
    # Traemos turnos de los próximos 2 días para filtrar en memoria (SQLite limit)
    turnos_proximos = Turno.objects.filter(
        fecha__gte=now.date(),
        fecha__lte=(now + datetime.timedelta(days=2)).date(),
        estado='PROGRAMADO',
        evaluado_25hs=False
    )
    
    evaluados = 0
    for turno in turnos_proximos:
        turno_datetime = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
        diff_hours = (turno_datetime - now).total_seconds() / 3600.0
        
        if 24 < diff_hours <= 25:
            inscriptos = Reserva.objects.filter(turno=turno, estado='CONFIRMADA').count()
            minimo = turno.clase.cupo_minimo
            reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
            
            if inscriptos < minimo:
                turno.estado = 'CANCELADO'
                turno.evaluado_25hs = True
                turno.save()
                
                for reserva in reservas:
                    reserva.estado = 'CANCELADA_TIEMPO'
                    reserva.save()
                    
                    suscripcion = reserva.suscripcion
                    suscripcion.clases_restantes += 1
                    if suscripcion.estado == 'AGOTADO':
                        suscripcion.estado = 'ACTIVO'
                    suscripcion.save()
                    
                    notificar_cancelacion_clase(reserva.usuario, turno)
                    
            elif inscriptos == minimo:
                turno.evaluado_25hs = True
                turno.save()
                
                for reserva in reservas:
                    notificar_recordatorio_asistencia(reserva.usuario, turno)
                
                # Simulamos enviar la alerta a 5 usuarios activos al azar que no esten en la clase
                usuarios_elegibles = Usuario.objects.filter(is_active=True, rol='CLIENTE').exclude(
                    id__in=reservas.values_list('usuario_id', flat=True)
                ).order_by('?')[:5]
                if usuarios_elegibles.exists():
                    notificar_alerta_cupo(usuarios_elegibles, turno)
                    
            else:
                turno.evaluado_25hs = True
                turno.save()
                
                for reserva in reservas:
                    notificar_recordatorio_asistencia(reserva.usuario, turno)
            
            evaluados += 1
            
    if evaluados > 0:
        print(f"[{now.strftime('%H:%M:%S')}] Evaluador automático: se procesaron {evaluados} clases.")

def notificar_profesores_diario():
    """
    Simula el envío de las clases del día siguiente a cada profesor.
    Se ejecutará idealmente una vez al día por la noche.
    """
    now = timezone.now()
    tomorrow = now.date() + datetime.timedelta(days=1)
    
    turnos_manana = Turno.objects.filter(
        fecha=tomorrow,
        estado='PROGRAMADO',
        profesor__isnull=False
    ).order_by('hora_inicio')
    
    profesores_turnos = {}
    for t in turnos_manana:
        if t.profesor not in profesores_turnos:
            profesores_turnos[t.profesor] = []
        profesores_turnos[t.profesor].append(t)
        
    for profesor, turnos in profesores_turnos.items():
        print(f"\n[NOTIFICACIÓN PROFESOR] Hola {profesor.nombre}, mañana dictarás:")
        for t in turnos:
            print(f"  - {t.hora_inicio.strftime('%H:%M')} : {t.clase.nombre}")
        print("¡Que tengas un excelente día de clases!\n")

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
