import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from core.models import Turno, Reserva
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from backend_core.hooks import registry
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from ...tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = (
        "Revisa turnos en las próximas 24 horas con bajo cupo (menos de 2 alumnas) y, "
        "en lugar de cancelar automáticamente, le envía una consulta a Deby (la dueña) "
        "por WhatsApp para que ella confirme o mantenga la clase."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--horas',
            type=int,
            default=24,
            help="Ventana límite de anticipación en horas (default: 24 hs)"
        )
        parser.add_argument(
            '--min-alumnas',
            type=int,
            default=2,
            help="Cupo mínimo requerido para dictar la clase (default: 2)"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simular sin aplicar cambios en la base de datos ni enviar mensajes"
        )

    def handle(self, *args, **options):
        horas_limite = options['horas']
        min_alumnas = options['min_alumnas']
        dry_run = options['dry_run']

        now = timezone.localtime()
        tz = now.tzinfo
        limite_dt = now + datetime.timedelta(hours=horas_limite)

        self.stdout.write(
            f"✦ [EVALUACIÓN BAJO CUPO] Buscando turnos entre {now.strftime('%d/%m %H:%M')} "
            f"y {limite_dt.strftime('%d/%m %H:%M')} hs con menos de {min_alumnas} alumnas..."
        )

        turnos = Turno.objects.filter(
            estado='PROGRAMADO',
            fecha__gte=now.date(),
            fecha__lte=limite_dt.date() + datetime.timedelta(days=1)
        ).select_related('clase').order_by('fecha', 'hora_inicio')

        client = WhatsAppClient()
        consultas_enviadas = 0
        clases_en_espera = 0
        clases_mantenidas_por_duena = 0

        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        clean_duena = "5491157691786"
        conversacion_duena, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_duena)

        for turno in turnos:
            clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
            if timezone.is_naive(clase_dt):
                clase_dt = timezone.make_aware(clase_dt, tz)

            # Evaluar solo turnos dentro de la ventana próxima (<24hs) y que no hayan empezado
            if not (now < clase_dt <= limite_dt):
                continue

            reservas_confirmadas = turno.reservas.filter(estado='CONFIRMADA').select_related('usuario')
            inscriptas = reservas_confirmadas.count()

            if inscriptas >= min_alumnas:
                # Clase con cupo suficiente (2 o 3 camillas ocupadas)
                continue

            dia_nom = dias_semana[turno.fecha.weekday()]
            hora_str = turno.hora_inicio.strftime('%H:%M')
            fecha_str = turno.fecha.strftime('%d/%m')

            prof_obj = obtener_profesor_de_turno(turno)
            prof_nombre = prof_obj.nombre if prof_obj else 'Sin asignar'
            profe_phone = None
            if prof_obj:
                profe_phone = getattr(prof_obj, 'telefono', None)
                if not profe_phone and getattr(prof_obj, 'usuario', None):
                    profe_phone = prof_obj.usuario.telefono

            # Verificar si ya existe una propuesta de cancelación previa para este turno
            propuesta_existente = RegistroAccionIA.objects.filter(
                tipo_accion='PROPUESTA_CANCELACION_BAJO_CUPO',
                metadata__turno_id=str(turno.id)
            ).order_by('-created_at').first()

            if propuesta_existente:
                if propuesta_existente.resultado == 'PENDIENTE':
                    self.stdout.write(
                        f"  ⏳ Esperando confirmación de Deby para {dia_nom} {fecha_str} {hora_str} hs ({inscriptas} inscriptas)."
                    )
                    clases_en_espera += 1
                    continue
                elif propuesta_existente.resultado == 'RECHAZADA':
                    self.stdout.write(
                        f"  🛡️ Deby indicó MANTENER clase {dia_nom} {fecha_str} {hora_str} hs activa. No se toca."
                    )
                    clases_mantenidas_por_duena += 1
                    continue
                elif propuesta_existente.resultado == 'CONFIRMADA':
                    continue

            # ==============================================================
            # NO CANCELAR DIRECTO: CONSULTAR A DEBY POR WHATSAPP PRIMERO
            # ==============================================================
            if inscriptas == 0:
                detalle_cupo = "no tiene alumnas inscriptas (0 camillas ocupadas)"
                nombre_display = None
                alumna_id = None
                reserva_id = None
                alumna_tel = None
            else:
                reserva = reservas_confirmadas.first()
                alumna = reserva.usuario
                nombre_display = (f"{alumna.nombre} {alumna.apellido}").strip() if alumna else (reserva.nombre_temporal or 'Alumna Manual')
                detalle_cupo = f"tiene solo 1 alumna inscripta ({nombre_display})"
                alumna_id = str(alumna.id) if alumna else None
                reserva_id = str(reserva.id)
                alumna_tel = alumna.telefono if alumna else reserva.telefono_temporal

            msg_duena = (
                f"¡Hola Deby! ✦ Consulta de Agenda:\n\n"
                f"El turno de *{turno.clase.nombre}* del *{dia_nom} {fecha_str} a las {hora_str} hs* (Prof. {prof_nombre}) "
                f"{detalle_cupo} a menos de 24 hs.\n\n"
                f"¿Confirmás cancelarla o la dejamos abierta?\n\n"
                f"👉 Respondé *\"CANCELAR\"* para darla de baja y avisarles, o *\"MANTENER\"* para dejarla activa ✨."
            )

            self.stdout.write(
                self.style.WARNING(
                    f"• Consultando a Deby para clase con bajo cupo: {dia_nom} {fecha_str} {hora_str} hs ({inscriptas} inscriptas)"
                )
            )

            if not dry_run:
                try:
                    client.send_text_message(clean_duena, msg_duena)

                    MensajeWhatsAppLog.objects.create(
                        conversacion=conversacion_duena,
                        direccion='SALIENTE',
                        agente_responsable='consulta_cancelacion_duena',
                        texto=msg_duena,
                        tools_ejecutadas=[f"propuesta_cancelacion_turno_{turno.id}"]
                    )

                    RegistroAccionIA.objects.create(
                        conversacion=conversacion_duena,
                        tipo_accion='PROPUESTA_CANCELACION_BAJO_CUPO',
                        resultado='PENDIENTE',
                        descripcion=f"Consulta enviada a Deby para confirmar cancelación de {dia_nom} {fecha_str} {hora_str}hs ({inscriptas} inscriptas).",
                        metadata={
                            'turno_id': str(turno.id),
                            'fecha': turno.fecha.strftime('%Y-%m-%d'),
                            'hora': turno.hora_inicio.strftime('%H:%M'),
                            'dia_nom': dia_nom,
                            'fecha_str': fecha_str,
                            'hora_str': hora_str,
                            'clase_nombre': turno.clase.nombre,
                            'inscriptas': inscriptas,
                            'profesor_nombre': prof_nombre,
                            'profesor_tel': profe_phone,
                            'alumna_nombre': nombre_display,
                            'alumna_id': alumna_id,
                            'reserva_id': reserva_id,
                            'alumna_tel': alumna_tel
                        }
                    )
                    consultas_enviadas += 1
                except Exception as e:
                    logger.error(f"Error enviando consulta de cancelación a Deby: {e}")

        resumen = (
            f"✦ [EVALUACIÓN FINALIZADA] Nuevas consultas enviadas a Deby: {consultas_enviadas} | "
            f"En espera de respuesta: {clases_en_espera} | "
            f"Mantenidas por decisión de Deby: {clases_mantenidas_por_duena}"
        )
        self.stdout.write(self.style.SUCCESS(resumen))
        logger.info(resumen)
