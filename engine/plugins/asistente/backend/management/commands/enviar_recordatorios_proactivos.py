import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Reserva, Turno
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog
from ...tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Envía recordatorios proactivos de clase por WhatsApp a las alumnas con turno confirmado hoy."

    def add_arguments(self, parser):
        parser.add_argument(
            '--horas',
            type=int,
            default=3,
            help="Ventana de anticipación en horas para avisar antes del inicio de la clase (default: 3 hs)"
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help="Forzar envío ignorando si ya fue enviado previamente"
        )

    def handle(self, *args, **options):
        horas_ventana = options['horas']
        forzar = options['forzar']

        ahora = timezone.localtime()
        hoy = ahora.date()
        limite_hora = (ahora + datetime.timedelta(hours=horas_ventana)).time()

        self.stdout.write(f"✦ Buscando turnos para hoy {hoy.strftime('%d/%m/%Y')} entre {ahora.strftime('%H:%M')} y {limite_hora.strftime('%H:%M')} hs...")

        reservas = Reserva.objects.filter(
            estado='CONFIRMADA',
            turno__fecha=hoy,
            turno__estado='PROGRAMADO',
            turno__hora_inicio__gte=ahora.time(),
            turno__hora_inicio__lte=limite_hora
        ).select_related('usuario', 'turno', 'turno__clase').order_by('turno__hora_inicio')

        enviados = 0
        omitidos = 0

        client = WhatsAppClient()

        for res in reservas:
            usuario = res.usuario
            turno = res.turno
            phone = getattr(usuario, 'telefono', '') or ''
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')

            if not clean_phone or len(clean_phone) < 8:
                self.stdout.write(f"- Alumna {usuario.nombre} {usuario.apellido} no tiene teléfono válido cargado. Omitiendo.")
                omitidos += 1
                continue

            conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)
            tag_recordatorio = f"recordatorio_turno_{turno.id}"

            # Verificar si ya se envió recordatorio para este turno
            if not forzar:
                ya_enviado = MensajeWhatsAppLog.objects.filter(
                    conversacion=conversacion,
                    direccion='SALIENTE',
                    tools_ejecutadas__contains=[tag_recordatorio]
                ).exists()
                if ya_enviado:
                    omitidos += 1
                    continue

            # Obtener nombre de la profesora
            prof_obj = obtener_profesor_de_turno(turno)
            profe_str = f" con la profe {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""

            nombre = usuario.nombre.strip() if usuario.nombre else "Hermosa"

            texto_recordatorio = (
                f"¡Hola {nombre}! ✦ Te recordamos que hoy tenés tu clase de {turno.clase.nombre} "
                f"a las {turno.hora_inicio.strftime('%H:%M')} hs{profe_str} ✨.\n\n"
                f"Te esperamos en nuestro estudio de Gral. Guido 1573. "
                f"Recordá llegar 5 minutitos antes para cambiarte con calma y arrancar tu práctica relajada ✦."
            )

            # Enviar mensaje
            ok = client.send_text_message(clean_phone, texto_recordatorio)

            # Registrar en log
            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion,
                direccion='SALIENTE',
                agente_responsable='recordatorio_proactivo',
                texto=texto_recordatorio,
                tools_ejecutadas=[tag_recordatorio]
            )

            if ok:
                enviados += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Recordatorio enviado a {nombre} ({clean_phone}) para las {turno.hora_inicio.strftime('%H:%M')} hs."))
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Intento de envío a {clean_phone} falló (o simulador activo)."))

        self.stdout.write(self.style.SUCCESS(f"✦ Finalizado: {enviados} recordatorios enviados, {omitidos} omitidos."))
