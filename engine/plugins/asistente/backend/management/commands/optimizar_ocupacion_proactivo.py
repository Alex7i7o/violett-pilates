import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
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

        # Buscar turnos con camillas libres (cupo_actual > 0) que esten PROGRAMADOS (no cancelados)
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
        contactadas_en_esta_corrida = set()
        slots_procesados = set()

        for turno in turnos_incompletos:
            slot_key = (turno.clase_id, turno.fecha, turno.hora_inicio)
            if slot_key in slots_procesados:
                continue
            slots_procesados.add(slot_key)

            dt_turno = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
            horas_hasta_clase = (dt_turno - now).total_seconds() / 3600
            if not (4 <= horas_hasta_clase <= 48):
                continue

            for sub in subs_con_credito:
                usuario = sub.usuario
                if not usuario or not usuario.telefono:
                    continue

                if usuario.id in contactadas_en_esta_corrida:
                    continue

                clean_phone = usuario.telefono.replace('+', '').replace(' ', '').replace('-', '')
                
                # Obtener o vincular conversacion de WhatsApp exacta de la alumna
                conv = ConversacionWhatsApp.objects.filter(usuario=usuario).first()
                if not conv and len(clean_phone) >= 8:
                    conv = ConversacionWhatsApp.objects.filter(telefono__endswith=clean_phone[-8:]).first()

                if not conv:
                    conv, _ = ConversacionWhatsApp.objects.get_or_create(
                        telefono=clean_phone,
                        defaults={'usuario': usuario, 'rol_detectado': 'ALUMNA'}
                    )
                elif conv.usuario != usuario:
                    conv.usuario = usuario
                    conv.save(update_fields=['usuario'])

                phone_destino = conv.telefono or clean_phone

                # 1. Regla de Vinculos Inseparables: si tiene pareja, solo ofrecer si hay al menos 2 camillas libres
                pareja = obtener_pareja_inseparable(usuario)
                if pareja and turno.cupo_actual < 2:
                    # No separar a madre e hija si solo queda 1 camilla
                    continue

                # 2. Verificar si ya tiene reserva ese dia
                ya_reservo = Reserva.objects.filter(
                    usuario=usuario,
                    turno__fecha=turno.fecha,
                    estado__in=['CONFIRMADA', 'TOMADA']
                ).exists()

                if ya_reservo:
                    continue

                # 3. Evitar escribirle a la misma persona mas de una vez en las ultimas 48 horas
                hace_48h = timezone.now() - datetime.timedelta(hours=48)
                
                ya_contactada = MensajeWhatsAppLog.objects.filter(
                    direccion='SALIENTE',
                    created_at__gte=hace_48h,
                    agente_responsable='optimizador_ocupacion_proactivo'
                ).filter(
                    Q(conversacion=conv) |
                    Q(conversacion__usuario=usuario) |
                    Q(conversacion__telefono=phone_destino) |
                    Q(conversacion__telefono=clean_phone)
                ).exists()

                if ya_contactada:
                    continue

                ya_ofertada = RegistroAccionIA.objects.filter(
                    tipo_accion='OFERTA_PROACTIVA',
                    created_at__gte=hace_48h
                ).filter(
                    Q(conversacion=conv) |
                    Q(conversacion__usuario=usuario) |
                    Q(payload__usuario_id=str(usuario.id))
                ).exists()

                if ya_ofertada:
                    continue

                # Evitar ofrecerle el mismo turno especifico dos veces
                ya_ofrecido_este_turno = RegistroAccionIA.objects.filter(
                    tipo_accion='OFERTA_PROACTIVA',
                    payload__turno_id=str(turno.id),
                    payload__usuario_id=str(usuario.id)
                ).exists()

                if ya_ofrecido_este_turno:
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
                    client.send_text_message(phone_destino, msg)
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
                    contactadas_en_esta_corrida.add(usuario.id)
                    contactadas_hoy += 1
                    self.stdout.write(f"Invitación proactiva enviada a {usuario.nombre} ({phone_destino}) para {dia_nom} {turno.hora_inicio.strftime('%H:%M')}")
                    break
                except Exception as e:
                    logger.error(f"Error enviando oferta proactiva a {phone_destino}: {e}")

        self.stdout.write(f"Proceso proactivo finalizado. Total invitadas: {contactadas_hoy}")
