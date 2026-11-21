import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ...models import ConversacionWhatsApp, MensajeWhatsAppLog

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Envía alertas proactivas por WhatsApp a las alumnas cuyo plan esté por vencer (<= 3 días) o con 1 crédito restante."

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help="Forzar envío ignorando si ya fue enviado previamente"
        )

    def handle(self, *args, **options):
        forzar = options['forzar']

        try:
            from plugins.membresias.backend.models import Suscripcion
        except ImportError:
            self.stdout.write(self.style.ERROR("Plugin de membresías no disponible."))
            return

        hoy = timezone.localdate()
        self.stdout.write(f"✦ Analizando suscripciones activas al {hoy.strftime('%d/%m/%Y')}...")

        suscripciones = Suscripcion.objects.filter(
            estado='ACTIVO',
            usuario__isnull=False,
            usuario__is_active=True
        ).select_related('usuario', 'plan')

        enviados = 0
        omitidos = 0
        client = WhatsAppClient()

        for sub in suscripciones:
            usuario = sub.usuario
            phone = getattr(usuario, 'telefono', None)
            if not phone:
                omitidos += 1
                continue

            clean_phone = str(phone).replace('+', '').replace(' ', '').replace('-', '')
            if len(clean_phone) < 8:
                omitidos += 1
                continue

            dias_restantes = (sub.fecha_vencimiento - hoy).days
            debe_avisar_vencimiento = (0 <= dias_restantes <= 3)
            debe_avisar_creditos = (sub.clases_restantes <= 1)

            if not (debe_avisar_vencimiento or debe_avisar_creditos):
                continue

            conversacion, _ = ConversacionWhatsApp.objects.get_or_create(
                telefono=clean_phone,
                defaults={'usuario': usuario, 'rol_detectado': 'ALUMNA'}
            )

            tag_alerta = f"alerta_sub_{sub.id}_venc_{sub.fecha_vencimiento}_cred_{sub.clases_restantes}"

            if not forzar:
                # Comprobar si ya se envió aviso en las últimas 72 horas para esta suscripción
                hace_3_dias = timezone.now() - datetime.timedelta(days=3)
                ya_enviado = MensajeWhatsAppLog.objects.filter(
                    conversacion=conversacion,
                    direccion='SALIENTE',
                    created_at__gte=hace_3_dias,
                    tools_ejecutadas__contains=[f"alerta_sub_{sub.id}"]
                ).exists()

                if ya_enviado:
                    omitidos += 1
                    continue

            nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
            plan_nom = sub.plan.nombre if hasattr(sub, 'plan') and hasattr(sub.plan, 'nombre') else "Abono Pilates"
            venc_str = sub.fecha_vencimiento.strftime('%d/%m')

            if sub.clases_restantes == 0:
                detalle_situacion = f"has completado todas las clases de tu *{plan_nom}*"
            elif sub.clases_restantes == 1:
                detalle_situacion = f"te queda tu última clase disponible de tu *{plan_nom}* (vence el {venc_str})"
            else:
                detalle_situacion = f"tu abono *{plan_nom}* vence en {dias_restantes} días (el {venc_str}) y aún contás con {sub.clases_restantes} clases"

            texto = (
                f"¡Hola {nombre}! ✦ Esperamos que estés teniendo una hermosa semana ✨.\n\n"
                f"Te escribimos con cariño desde Violett Pilates para recordarte que {detalle_situacion}.\n\n"
                f"Si deseás renovar para continuar con tu práctica y asegurar tus camillas habituales, "
                f"podés avisarnos por acá o gestionarlo cómodamente desde tu app 🌸.\n\n"
                f"¡Estamos a tu disposición para lo que necesites!"
            )

            ok = client.send_text_message(clean_phone, texto)
            if not ok:
                # Reintentar con plantilla si ventana 24hs está cerrada
                try:
                    components = [{
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": nombre},
                            {"type": "text", "text": plan_nom},
                            {"type": "text", "text": venc_str}
                        ]
                    }]
                    client._send_template(clean_phone, "recordatorio_vencimiento_plan", components)
                except Exception as ex_t:
                    logger.warning(f"Error fallback plantilla vencimiento a {clean_phone}: {ex_t}")

            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion,
                direccion='SALIENTE',
                agente_responsable='alerta_vencimiento_abonos',
                texto=texto,
                tools_ejecutadas=[tag_alerta, f"alerta_sub_{sub.id}"]
            )

            enviados += 1
            self.stdout.write(self.style.SUCCESS(f"✓ Alerta enviada a {nombre} ({clean_phone}) - Plan {plan_nom}"))

        self.stdout.write(self.style.SUCCESS(f"✦ Finalizado: {enviados} alertas enviadas, {omitidos} omitidas."))
