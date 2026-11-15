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

            # 1. Actualizar reservas pasadas a TOMADAS
            actualizar_reservas_pasadas_a_tomadas(usuario=usuario)

            # 2. Clases tomadas en este ciclo
            clases_tomadas_qs = Reserva.objects.filter(
                usuario=usuario,
                estado='TOMADA',
                turno__fecha__lte=sub.fecha_vencimiento
            )
            if sub.fecha_inicio:
                clases_tomadas_qs = clases_tomadas_qs.filter(turno__fecha__gte=sub.fecha_inicio - datetime.timedelta(days=7))
            clases_tomadas = clases_tomadas_qs.count()

            # 3. Clases pendientes estrictamente a futuro dentro de la vigencia del plan
            clases_pendientes = Reserva.objects.filter(
                usuario=usuario,
                estado='CONFIRMADA',
                turno__fecha__lte=sub.fecha_vencimiento
            ).filter(
                Q(turno__fecha__gt=today) |
                Q(turno__fecha=today, turno__hora_inicio__gte=now_time)
            ).count()

            # 4. Clases canceladas en este ciclo (informativo)
            clases_canceladas = Reserva.objects.filter(
                usuario=usuario,
                estado__startswith='CANCELADA',
                turno__fecha__lte=sub.fecha_vencimiento
            ).count()

            # 5. Cálculo real de créditos
            clases_totales = sub.plan.cantidad_clases
            creditos_reales = max(0, clases_totales - (clases_tomadas + clases_pendientes))
            clases_pendientes_efectivas = min(clases_pendientes, max(0, clases_totales - clases_tomadas))

            estado_original = sub.estado
            restantes_original = sub.clases_restantes

            nuevo_estado = 'ACTIVO' if creditos_reales > 0 else 'AGOTADO'

            sub.clases_restantes = creditos_reales
            sub.estado = nuevo_estado
            sub.save(update_fields=['clases_restantes', 'estado'])

            self.stdout.write(self.style.SUCCESS(
                f"[OK] {usuario.nombre} {usuario.apellido} ({usuario.email}):\n"
                f"     Plan: {sub.plan.nombre} (Total: {clases_totales})\n"
                f"     Tomadas: {clases_tomadas} | Canceladas: {clases_canceladas} | Pendientes por tomar: {clases_pendientes_efectivas}\n"
                f"     Créditos disponibles: {restantes_original} -> {creditos_reales} | Estado: {estado_original} -> {nuevo_estado}"
            ))

        self.stdout.write(self.style.SUCCESS("=== RECONCILIACION FINALIZADA CON EXITO ==="))
