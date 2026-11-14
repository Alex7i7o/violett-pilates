from django.core.management.base import BaseCommand
from django.utils import timezone
from core.services import generar_turnos_desde_plantillas

class Command(BaseCommand):
    help = "Sincroniza y asegura que las clases futuras de los próximos N días estén generadas en la Agenda a partir del Esquema Semanal."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Cantidad de días hacia adelante a sincronizar (por defecto 30 días)'
        )

    def handle(self, *args, **options):
        dias = options.get('dias', 30)
        now = timezone.localdate()
        self.stdout.write(f"✦ [{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando sincronización de agenda futura ({dias} días desde {now})...")
        
        nuevos = generar_turnos_desde_plantillas(dias=dias)
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ Sincronización completada exitosamente. Se crearon {nuevos} turnos nuevos en la Agenda."
        ))
