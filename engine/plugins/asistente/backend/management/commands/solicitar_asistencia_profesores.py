from django.core.management.base import BaseCommand
from ...services.asistencia_profesores import solicitar_asistencia_clases_finalizadas

class Command(BaseCommand):
    help = (
        "Revisa las clases dictadas hoy que ya finalizaron y cuyas alumnas aún tienen reserva "
        "en estado 'CONFIRMADA' (sin asistencia tomada), y le envía un WhatsApp a la profesora a cargo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simular sin enviar mensajes reales de WhatsApp"
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        self.stdout.write("✦ [ASISTENCIA PROFESORES] Verificando clases finalizadas sin asistencia...")
        enviados = solicitar_asistencia_clases_finalizadas(dry_run=dry_run)
        self.stdout.write(self.style.SUCCESS(f"✦ [ASISTENCIA PROFESORES] Proceso finalizado. Mensajes enviados: {enviados}"))
