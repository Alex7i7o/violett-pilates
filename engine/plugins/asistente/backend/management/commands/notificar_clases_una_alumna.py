import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Turno
from ...services.notificaciones_duena import notificar_duena_clase_con_una_alumna

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = (
        "Revisa las clases de los próximos 7 días (1 semana) y le notifica a Débora por WhatsApp "
        "aquellas que tengan solo 1 alumna inscripta."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help="Ventana de días hacia adelante a evaluar (default: 7 días / 1 semana)"
        )

    def handle(self, *args, **options):
        dias_adelante = options['dias']
        now = timezone.localtime()
        tz = now.tzinfo
        limite_dt = now + datetime.timedelta(days=dias_adelante)

        self.stdout.write(
            f"✦ [REVISIÓN CLASES 1 ALUMNA] Buscando turnos entre {now.strftime('%d/%m')} "
            f"y {limite_dt.strftime('%d/%m')} con exactamente 1 alumna..."
        )

        turnos = Turno.objects.filter(
            estado='PROGRAMADO',
            fecha__gte=now.date(),
            fecha__lte=limite_dt.date()
        ).select_related('clase').order_by('fecha', 'hora_inicio')

        evaluados = 0
        alertados = 0

        for turno in turnos:
            clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
            if timezone.is_naive(clase_dt):
                clase_dt = timezone.make_aware(clase_dt, tz)

            if clase_dt <= now or clase_dt > limite_dt:
                continue

            evaluados += 1
            cant = turno.reservas.filter(estado='CONFIRMADA').count()
            if cant == 1:
                notificar_duena_clase_con_una_alumna(turno, motivo='revision_semanal')
                alertados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✦ [FINALIZADO] Turnos evaluados: {evaluados} | Clases con 1 alumna notificadas: {alertados}"
            )
        )
