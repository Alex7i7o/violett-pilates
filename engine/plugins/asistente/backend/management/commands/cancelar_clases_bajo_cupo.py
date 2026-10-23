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
        "Revisa turnos en las próximas 24 horas y cancela automáticamente aquellos "
        "que estén vacíos (0 alumnas) o tengan 1 sola alumna inscripta, reintegrando "
        "el crédito y notificando por WhatsApp."
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
            f"✦ [AUTO-CANCELACIÓN] Buscando turnos entre {now.strftime('%d/%m %H:%M')} "
            f"y {limite_dt.strftime('%d/%m %H:%M')} hs con menos de {min_alumnas} alumnas..."
        )

        turnos = Turno.objects.filter(
            estado='PROGRAMADO',
            fecha__gte=now.date(),
            fecha__lte=limite_dt.date() + datetime.timedelta(days=1)
        ).select_related('clase').order_by('fecha', 'hora_inicio')

        client = WhatsAppClient()
        clases_vacias_canceladas = 0
        clases_1_alumna_canceladas = 0
        alumnas_notificadas = 0
        profesores_notificados = 0

        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        for turno in turnos:
            clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
            if timezone.is_naive(clase_dt):
                clase_dt = timezone.make_aware(clase_dt, tz)

            # Evaluar solo turnos que caigan dentro de la ventana de < 24hs y que aún no hayan empezado
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
            profe_phone = None
            if prof_obj:
                profe_phone = getattr(prof_obj, 'telefono', None)
                if not profe_phone and getattr(prof_obj, 'usuario', None):
                    profe_phone = prof_obj.usuario.telefono

            # ==========================================
            # ESCENARIO A: CLASE COMPLETAMENTE VACÍA (0)
            # ==========================================
            if inscriptas == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"• Cancelando clase vacía: {dia_nom} {fecha_str} a las {hora_str} hs ({turno.clase.nombre})"
                    )
                )

                if not dry_run:
                    turno.estado = 'CANCELADO'
                    turno.save()

                    # Notificar a la profesora para que no viaje al estudio
                    if profe_phone:
                        clean_profe = str(profe_phone).replace('+', '').replace(' ', '').replace('-', '')
                        msg_profe = (
                            f"¡Hola {prof_obj.nombre}! ✦ Te avisamos que el turno de {turno.clase.nombre} "
                            f"del {dia_nom} {fecha_str} a las {hora_str} hs fue cancelado automáticamente "
                            f"al encontrarse sin alumnas inscriptas a menos de 24 hs. ¡Que tengas lindo día!"
                        )
                        client.send_text_message(clean_profe, msg_profe)
                        profesores_notificados += 1

                    RegistroAccionIA.objects.create(
                        tipo_accion='TURNO_CANCELADO',
                        descripcion=f"Turno vacío del {fecha_str} {hora_str}hs cancelado automáticamente (<24hs)."
                    )

                clases_vacias_canceladas += 1

            # ==============================================
            # ESCENARIO B: CLASE CON 1 SOLA ALUMNA (< min)
            # ==============================================
            elif inscriptas == 1:
                reserva = reservas_confirmadas.first()
                alumna = reserva.usuario
                nombre_display = (f"{alumna.nombre} {alumna.apellido}").strip() if alumna else (reserva.nombre_temporal or 'Alumna Manual')
                self.stdout.write(
                    self.style.WARNING(
                        f"• Cancelando clase con 1 sola alumna ({nombre_display}): "
                        f"{dia_nom} {fecha_str} a las {hora_str} hs ({turno.clase.nombre})"
                    )
                )

                if not dry_run:
                    with transaction.atomic():
                        turno.estado = 'CANCELADO'
                        turno.save()

                        reserva.estado = 'CANCELADA_TIEMPO'
                        reserva.save()

                        # Reintegrar crédito a la alumna si es registrada
                        if alumna:
                            try:
                                from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
                                rm = ReservaMembresia.objects.filter(reserva=reserva).first()
                                if rm:
                                    sub = rm.suscripcion
                                    sub.clases_restantes += 1
                                    if sub.estado == 'AGOTADO':
                                        sub.estado = 'ACTIVO'
                                    sub.save()
                                    rm.delete()
                                else:
                                    sub = Suscripcion.objects.filter(
                                        usuario=alumna,
                                        estado__in=['ACTIVO', 'AGOTADO']
                                    ).order_by('-fecha_inicio').first()
                                    if sub:
                                        sub.clases_restantes += 1
                                        if sub.estado == 'AGOTADO':
                                            sub.estado = 'ACTIVO'
                                        sub.save()
                            except Exception as e:
                                logger.error(f"Error reintegrando crédito a {alumna}: {e}")

                        registry.execute('reserva_cancelada_a_tiempo', reserva)
                        registry.execute('turno_cancelado_por_falta_cupo', turno)

                    # Notificar a la alumna por WhatsApp con tono Pilates Princess
                    tel_raw = alumna.telefono if alumna else reserva.telefono_temporal
                    clean_phone = tel_raw.replace('+', '').replace(' ', '').replace('-', '') if tel_raw else ''
                    if clean_phone and len(clean_phone) >= 8:
                        conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)
                        nombre_alumna = alumna.nombre.strip() if (alumna and alumna.nombre) else (reserva.nombre_temporal.strip() if reserva.nombre_temporal else "Hermosa")

                        msg_alumna = (
                            f"¡Hola {nombre_alumna}! ✦ Te escribimos desde Violett Pilates.\n\n"
                            f"Te contamos que para el turno de {turno.clase.nombre} del {dia_nom} {fecha_str} "
                            f"a las {hora_str} hs no se alcanzó el cupo mínimo requerido para dictar la clase (mínimo 2 alumnas).\n\n"
                            f"Por este motivo, la clase fue cancelada y tu crédito ya fue reintegrado automáticamente a tu abono ✦. "
                            f"Tenés tu clase lista para reprogramar en el horario que más cómodo te quede.\n\n"
                            f"Si querés, decime qué día y horario preferís y te paso las opciones disponibles para anotarte ✨."
                        )
                        client.send_text_message(clean_phone, msg_alumna)
                        MensajeWhatsAppLog.objects.create(
                            conversacion=conversacion,
                            direccion='SALIENTE',
                            agente_responsable='cancelacion_bajo_cupo',
                            texto=msg_alumna,
                            tools_ejecutadas=[f"cancelacion_turno_{turno.id}"]
                        )
                        alumnas_notificadas += 1

                    # Notificar a la profesora
                    if profe_phone:
                        clean_profe = str(profe_phone).replace('+', '').replace(' ', '').replace('-', '')
                        msg_profe = (
                            f"¡Hola {prof_obj.nombre}! ✦ Te avisamos que el turno de {turno.clase.nombre} "
                            f"del {dia_nom} {fecha_str} a las {hora_str} hs fue cancelado por no alcanzar el "
                            f"cupo mínimo (1 sola alumna inscripta). La alumna fue notificada y su crédito reintegrado."
                        )
                        client.send_text_message(clean_profe, msg_profe)
                        profesores_notificados += 1

                    RegistroAccionIA.objects.create(
                        tipo_accion='TURNO_CANCELADO',
                        descripcion=f"Turno {fecha_str} {hora_str}hs cancelado por bajo cupo (1 alumna: {alumna.nombre}). Crédito devuelto."
                    )

                clases_1_alumna_canceladas += 1

        resumen = (
            f"✦ [AUTO-CANCELACIÓN FINALIZADA] Clases vacías canceladas: {clases_vacias_canceladas} | "
            f"Clases de 1 alumna canceladas: {clases_1_alumna_canceladas} | "
            f"Alumnas notificadas y reintegradas: {alumnas_notificadas} | "
            f"Profesores avisados: {profesores_notificados}"
        )
        self.stdout.write(self.style.SUCCESS(resumen))
        logger.info(resumen)
