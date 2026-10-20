import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Turno, Reserva, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ...config_loader import get_asistente_config
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from ...tools.optimizacion_tools import obtener_pareja_inseparable

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitorea turnos en las proximas 24-48h con camillas libres y contacta proactivamente a alumnas con creditos para llenar el estudio.'

    def handle(self, *args, **kwargs):
        config = get_asistente_config()
        if not config.get('modos_activos', {}).get('llenado_proactivo_camillas', True):
            self.stdout.write("Modo de llenado proactivo desactivado en client-config.")
            return

        now = timezone.now()
        hoy = timezone.localdate()
        limite_futuro = hoy + datetime.timedelta(days=2)

        # Buscar turnos con camillas libres (cupo_actual > 0)
        turnos_incompletos = Turno.objects.filter(
            fecha__gte=hoy,
            fecha__lte=limite_futuro,
            estado='PROGRAMADO',
            cupo_actual__gt=0
        ).select_related('clase').order_by('fecha', 'hora_inicio')

        if not turnos_incompletos.exists():
            self.stdout.write("Todos los turnos están 100% completos o no hay turnos programados.")
            return

        try:
            from plugins.membresias.backend.models import Suscripcion
        except ImportError:
            return

        # Alumnas activas con créditos disponibles
        subs_con_credito = Suscripcion.objects.filter(
            estado='ACTIVO',
            clases_restantes__gt=0,
            fecha_vencimiento__gte=hoy
        ).select_related('usuario')

        client = WhatsAppClient()
        contactadas_hoy = 0

        for turno in turnos_incompletos:
            dt_turno = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
            horas_hasta_clase = (dt_turno - now).total_seconds() / 3600
            if not (4 <= horas_hasta_clase <= 48):
                continue

            for sub in subs_con_credito:
                usuario = sub.usuario
                if not usuario.telefono:
                    continue

                clean_phone = usuario.telefono.replace('+', '').replace(' ', '').replace('-', '')
                
                # 1. Regla de Vínculos Inseparables: si tiene pareja, solo ofrecer si hay al menos 2 camillas libres
                pareja = obtener_pareja_inseparable(usuario)
                if pareja and turno.cupo_actual < 2:
                    # No separar a madre e hija si solo queda 1 camilla
                    continue

                # 2. Verificar si ya tiene reserva ese día
                ya_reservo = Reserva.objects.filter(
                    usuario=usuario,
                    turno__fecha=turno.fecha,
                    estado='CONFIRMADA'
                ).exists()

                if ya_reservo:
                    continue

                # 3. Evitar escribirle a la misma persona más de una vez en las últimas 24 horas
                hace_24h = timezone.now() - datetime.timedelta(hours=24)
                ya_contactada = MensajeWhatsAppLog.objects.filter(
                    conversacion__telefono=clean_phone,
                    direccion='SALIENTE',
                    created_at__gte=hace_24h
                ).exists()

                if ya_contactada:
                    continue

                dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                dia_nom = dias[turno.fecha.weekday()]
                nombre_alumna = usuario.nombre or "Hola"

                if pareja:
                    msg = (
                        f"¡Hola {nombre_alumna}! ✦ Se liberaron camillas en Reformer para el {dia_nom} {turno.fecha.strftime('%d/%m')} "
                        f"a las {turno.hora_inicio.strftime('%H:%M')} hs en {turno.clase.nombre}.\n\n"
                        f"Como vienen juntas con {pareja.nombre}, ¿les gustaría que les reserve dos camillas para esa clase? "
                        f"Si quieren venir, respondeme 'Sí, reservanos' y se las aseguro."
                    )
                else:
                    msg = (
                        f"¡Hola {nombre_alumna}! ✦ Se acaba de liberar una camilla para el {dia_nom} {turno.fecha.strftime('%d/%m')} "
                        f"a las {turno.hora_inicio.strftime('%H:%M')} hs en {turno.clase.nombre}.\n\n"
                        f"Como tenés {sub.clases_restantes} clases disponibles en tu plan, ¿te gustaría que te reserve el lugar? "
                        f"Si querés venir, respondeme 'Sí, reservame' y te la aseguro."
                    )

                try:
                    client.send_text_message(clean_phone, msg)
                    conv, _ = ConversacionWhatsApp.objects.get_or_create(
                        telefono=clean_phone,
                        defaults={'usuario': usuario, 'rol_detectado': 'ALUMNA'}
                    )
                    MensajeWhatsAppLog.objects.create(
                        conversacion=conv,
                        direccion='SALIENTE',
                        agente_responsable='optimizador_ocupacion_proactivo',
                        texto=msg
                    )
                    RegistroAccionIA.objects.create(
                        conversacion=conv,
                        tipo_accion='OFERTA_PROACTIVA',
                        descripcion=f"Camilla libre ofrecida a {usuario.nombre} para turno {turno.fecha} {turno.hora_inicio}",
                        payload={'turno_id': str(turno.id), 'usuario_id': str(usuario.id)}
                    )
                    contactadas_hoy += 1
                    self.stdout.write(f"Invitación proactiva enviada a {usuario.nombre} ({clean_phone}) para {dia_nom} {turno.hora_inicio.strftime('%H:%M')}")
                    break
                except Exception as e:
                    logger.error(f"Error enviando oferta proactiva a {clean_phone}: {e}")

        self.stdout.write(f"Proceso proactivo finalizado. Total invitadas: {contactadas_hoy}")
