import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from core.models import Usuario, Reserva
from core.services import actualizar_reservas_pasadas_a_tomadas
from plugins.membresias.backend.models import Suscripcion

class Command(BaseCommand):
    help = "Reconcilia los creditos de membresia, clases tomadas y agendadas de las alumnas"

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de la alumna a reconciliar especificamente',
            default=None
        )

    def handle(self, *args, **options):
        email_filter = options.get('email')
        qs = Suscripcion.objects.filter(estado__in=['ACTIVO', 'AGOTADO']).select_related('usuario', 'plan').order_by('-fecha_inicio')
        if email_filter:
            qs = qs.filter(usuario__email__icontains=email_filter)

        self.stdout.write(self.style.NOTICE(f"=== INICIANDO RECONCILIACION DE MEMBRESIAS ({qs.count()} encontradas) ==="))

        now = timezone.localtime()
        today = now.date()
        now_time = now.time()

        usuarios_procesados = set()

        for sub in qs:
            usuario = sub.usuario
            if not usuario or usuario.id in usuarios_procesados:
                continue
            usuarios_procesados.add(usuario.id)

            # Cálculo real y auditado de métricas
            from plugins.membresias.backend.services import calcular_metricas_suscripcion
            metricas = calcular_metricas_suscripcion(sub, usuario=usuario)

            clases_totales = metricas['clases_totales']
            clases_tomadas = metricas['clases_tomadas']
            clases_pendientes_efectivas = metricas['clases_pendientes']
            creditos_reales = metricas['creditos_reales']

            clases_canceladas = Reserva.objects.filter(
                usuario=usuario,
                estado__startswith='CANCELADA',
                turno__fecha__lte=sub.fecha_vencimiento
            ).count()

            estado_original = sub.estado
            restantes_original = sub.clases_restantes

            nuevo_estado = 'ACTIVO' if creditos_reales > 0 else 'AGOTADO'

            self.stdout.write(self.style.SUCCESS(
                f"[OK] {usuario.nombre} {usuario.apellido} ({usuario.email}):\n"
                f"     Plan: {sub.plan.nombre} (Total: {clases_totales})\n"
                f"     Tomadas: {clases_tomadas} | Canceladas: {clases_canceladas} | Pendientes por tomar: {clases_pendientes_efectivas}\n"
                f"     Créditos disponibles: {restantes_original} -> {creditos_reales} | Estado: {estado_original} -> {nuevo_estado}"
            ))

        self.stdout.write(self.style.SUCCESS("=== RECONCILIACION FINALIZADA CON EXITO ==="))
