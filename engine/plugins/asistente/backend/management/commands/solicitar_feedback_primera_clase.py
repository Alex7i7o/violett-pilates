import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Reserva, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Envía una solicitud cálida de feedback por WhatsApp a las alumnas que tuvieron hoy su primera clase en el estudio (20:30 hs)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help="Forzar envío ignorando comprobaciones de log previo"
        )

    def handle(self, *args, **options):
        forzar = options['forzar']
        hoy = timezone.localdate()

        self.stdout.write(f"✦ Buscando alumnas con primera clase realizada hoy {hoy.strftime('%d/%m/%Y')}...")

        # Alumnas que tuvieron clase hoy
        reservas_hoy = Reserva.objects.filter(
            turno__fecha=hoy,
            estado__in=['TOMADA', 'CONFIRMADA'],
            usuario__isnull=False
        ).select_related('usuario', 'turno__clase')

        enviados = 0
        omitidos = 0
        client = WhatsAppClient()

        for res in reservas_hoy:
            usuario = res.usuario
            phone = getattr(usuario, 'telefono', None)
            if not phone:
                omitidos += 1
                continue

            clean_phone = str(phone).replace('+', '').replace(' ', '').replace('-', '')
            if len(clean_phone) < 8:
                omitidos += 1
                continue

            # Comprobar si esta fue realmente su primera clase en el estudio
            total_clases_historicas = Reserva.objects.filter(
                usuario=usuario,
                estado__in=['TOMADA', 'CONFIRMADA']
            ).count()

            # Solo aplica si es su primera clase (o a lo sumo 1 clase tomada)
            if total_clases_historicas > 1 and not forzar:
                omitidos += 1
                continue

            tag_feedback = f"feedback_primera_clase_{usuario.id}"

            if not forzar:
                ya_enviado = MensajeWhatsAppLog.objects.filter(
                    tools_ejecutadas__contains=[tag_feedback]
                ).exists()
                if ya_enviado:
                    omitidos += 1
                    continue

            nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
            clase_nom = res.turno.clase.nombre if res.turno and res.turno.clase else "Pilates Reformer"

            texto = (
                f"¡Hola {nombre}! ✦ ¡Esperamos que hayas disfrutado muchísimo de tu primera clase de *{clase_nom}* de hoy en Violett Pilates! ✨\n\n"
                f"Nos encantaría saber cómo te sentiste, cómo respondió tu cuerpo en el Reformer y si la práctica cumplió con lo que buscabas.\n\n"
                f"Cualquier sensación, comentario o sugerencia que quieras compartirnos nos ayuda muchísimo a seguir cuidando cada detalle de tu experiencia 🌸.\n\n"
                f"¡Te esperamos con mucho cariño en tu próxima sesión!"
            )

            conversacion, _ = ConversacionWhatsApp.objects.get_or_create(
                telefono=clean_phone,
                defaults={'usuario': usuario, 'rol_detectado': 'ALUMNA'}
            )

            ok = client.send_text_message(clean_phone, texto)

            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion,
                direccion='SALIENTE',
                agente_responsable='feedback_primera_clase',
                texto=texto,
                tools_ejecutadas=[tag_feedback]
            )

            RegistroAccionIA.objects.create(
                tipo_accion='OFERTA_PROACTIVA',
                descripcion=f"Solicitud de feedback de primera clase enviada a {usuario.nombre} {usuario.apellido}.",
                payload={'tag': tag_feedback, 'usuario_id': str(usuario.id), 'fecha': hoy.isoformat()}
            )

            enviados += 1
            self.stdout.write(self.style.SUCCESS(f"✓ Feedback solicitado a {nombre} ({clean_phone})."))

        self.stdout.write(self.style.SUCCESS(f"✦ Finalizado: {enviados} solicitudes de feedback enviadas, {omitidos} omitidas."))
