import datetime
import logging
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Turno, Reserva
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from ...tools.profesores_tools import resolver_fecha, obtener_profesor_de_turno

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = (
        "Envía cada noche a los profesores de Violett Pilates un WhatsApp con el cronograma "
        "detallado de sus clases asignadas para el día de mañana (horarios y alumnas inscriptas)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            default='mañana',
            help="Fecha a consultar (default: 'mañana', o 'hoy', o 'YYYY-MM-DD')"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simular el envío y mostrar los mensajes en la consola sin enviar WhatsApp"
        )
        parser.add_argument(
            '--incluir-sin-clases',
            action='store_true',
            help="Enviar mensaje también a los profesores que no tienen clases asignadas mañana"
        )

    def handle(self, *args, **options):
        fecha_str = options['fecha']
        dry_run = options['dry_run']
        incluir_sin_clases = options['incluir_sin_clases']

        target_date = resolver_fecha(fecha_str)

        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_nom = dias_semana[target_date.weekday()]
        fecha_formateada = target_date.strftime('%d/%m')

        self.stdout.write(
            f"✦ [RECORDATORIO PROFESORES] Procesando agenda para {dia_nom} {fecha_formateada}..."
        )

        try:
            from plugins.profesores.backend.models import Profesor
        except ImportError:
            self.stdout.write(self.style.ERROR("Error: Plugin de profesores no disponible."))
            return

        profesores_activos = Profesor.objects.filter(is_active=True)
        if not profesores_activos.exists():
            self.stdout.write("No hay profesores activos registrados.")
            return

        # Buscar todos los turnos programados para la fecha
        turnos_dia = Turno.objects.filter(
            fecha=target_date,
            estado='PROGRAMADO'
        ).select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').order_by('hora_inicio')

        # Agrupar turnos por profesor
        turnos_por_profe = defaultdict(list)
        for t in turnos_dia:
            prof = obtener_profesor_de_turno(t)
            if prof:
                turnos_por_profe[str(prof.id)].append(t)

        client = WhatsAppClient()
        enviados = 0
        omitidos = 0

        for profe in profesores_activos:
            # Obtener teléfono
            phone = getattr(profe, 'telefono', None)
            if not phone and getattr(profe, 'usuario', None):
                phone = profe.usuario.telefono

            clean_phone = str(phone or '').replace('+', '').replace(' ', '').replace('-', '')
            if not clean_phone or len(clean_phone) < 8:
                self.stdout.write(self.style.WARNING(f"- Profe {profe.nombre} {profe.apellido} no tiene teléfono válido. Omitiendo."))
                omitidos += 1
                continue

            profe_turnos = turnos_por_profe.get(str(profe.id), [])

            # Si no tiene clases
            if not profe_turnos:
                if incluir_sin_clases:
                    msg = (
                        f"¡Hola {profe.nombre}! ✦ Te recordamos que para mañana {dia_nom} {fecha_formateada} "
                        f"no tenés clases programadas en Violett Pilates. ¡Que tengas un excelente descanso! ✨"
                    )
                    if dry_run:
                        self.stdout.write(f"\n[DRY-RUN] Mensaje a {profe.nombre} ({clean_phone}):\n{msg}\n")
                    else:
                        client.send_text_message(clean_phone, msg)
                        enviados += 1
                else:
                    self.stdout.write(f"- Profe {profe.nombre} {profe.apellido} no tiene clases mañana.")
                continue

            # Construir resumen de clases
            lineas_clases = []
            for t in profe_turnos:
                reservas_conf = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
                inscriptas = len(reservas_conf)

                nombres = []
                for r in reservas_conf:
                    if r.usuario:
                        nombres.append(f"{r.usuario.nombre} {r.usuario.apellido}".strip())
                    elif getattr(r, 'nombre_temporal', None):
                        nombres.append(f"{r.nombre_temporal} (Manual)")

                alumnas_str = ", ".join(nombres) if nombres else "Sin alumnas aún"
                hora_ini = t.hora_inicio.strftime('%H:%M')
                hora_fin = t.hora_fin.strftime('%H:%M') if t.hora_fin else ""
                rango_hora = f"{hora_ini} a {hora_fin} hs" if hora_fin else f"{hora_ini} hs"

                lineas_clases.append(
                    f"• {rango_hora} - {t.clase.nombre} ({inscriptas}/3 camillas)\n"
                    f"  Alumnas: {alumnas_str}"
                )

            total_clases = len(profe_turnos)
            clases_bloque = "\n\n".join(lineas_clases)

            msg = (
                f"¡Hola {profe.nombre}! ✦ Te compartimos tu cronograma de clases para mañana "
                f"{dia_nom} {fecha_formateada} en Violett Pilates ✨:\n\n"
                f"{clases_bloque}\n\n"
                f"Total: {total_clases} {'clase' if total_clases == 1 else 'clases'} asignada{'s' if total_clases > 1 else ''}.\n"
                f"¡Que tengas una hermosa jornada mañana! ✦"
            )

            if dry_run:
                self.stdout.write(f"\n[DRY-RUN] Mensaje a {profe.nombre} ({clean_phone}):\n{msg}\n")
                enviados += 1
            else:
                ok = client.send_text_message(clean_phone, msg)
                conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)
                MensajeWhatsAppLog.objects.create(
                    conversacion=conversacion,
                    direccion='SALIENTE',
                    agente_responsable='recordatorio_nocturno_profe',
                    texto=msg,
                    tools_ejecutadas=[f"agenda_profe_{target_date.isoformat()}"]
                )
                RegistroAccionIA.objects.create(
                    tipo_accion='REPORTE_PROFE',
                    descripcion=f"Agenda enviada a profe {profe.nombre} ({total_clases} clases para {fecha_formateada})."
                )
                if ok:
                    self.stdout.write(self.style.SUCCESS(f"✓ Recordatorio enviado a {profe.nombre} ({clean_phone})."))
                    enviados += 1
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Falló el envío a {profe.nombre} ({clean_phone})."))

        resumen = f"✦ Finalizado: {enviados} profesores notificados, {omitidos} omitidos."
        self.stdout.write(self.style.SUCCESS(resumen))
        logger.info(resumen)
