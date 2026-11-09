from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import PlantillaTurno, Turno, Reserva
from backend_core.hooks import registry

class Command(BaseCommand):
    help = "Purga plantillas inactivas y turnos futuros huérfanos sin inscriptos para sincronizar al 100% el frontend con WhatsApp."

    def handle(self, *args, **options):
        now = timezone.localdate()
        self.stdout.write("✦ Iniciando sincronización y purga de horarios...")

        # 1. Purgar plantillas inactivas
        inactivas = PlantillaTurno.objects.filter(is_active=False)
        count_plantillas = inactivas.count()
        for p in inactivas:
            # Desactivar recurrencias asociadas
            try:
                registry.execute(
                    "after_slot_destroyed", 
                    {}, 
                    clase_id=p.clase_id, 
                    dia_semana=p.dia_semana, 
                    hora_inicio=p.hora_inicio
                )
            except Exception:
                pass
            # Eliminar turnos futuros de esta plantilla inactiva
            Turno.objects.filter(
                clase_id=p.clase_id,
                fecha__gte=now,
                hora_inicio=p.hora_inicio
            ).filter(reservas__isnull=True).delete()
            p.delete()

        # 2. Purgar turnos futuros específicos de Sábados a las 17:00 que quedaron sin inscriptos
        sabados_17 = [
            t for t in Turno.objects.filter(fecha__gte=now, hora_inicio__hour=17)
            if t.fecha.isoweekday() == 6
        ]
        count_turnos = 0
        for t in sabados_17:
            # Si no tiene reservas activas, eliminarlo
            activas = t.reservas.exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA'])
            if not activas.exists():
                t.delete()
                count_turnos += 1

        self.stdout.write(self.style.SUCCESS(
            f"✦ Sincronización finalizada: {count_plantillas} plantillas inactivas purgadas y {count_turnos} turnos vacíos de los sábados eliminados."
        ))
