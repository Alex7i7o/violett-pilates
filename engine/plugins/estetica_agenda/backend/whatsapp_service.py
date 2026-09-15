import logging
import os
import requests

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self):
        self.token = os.environ.get('WHATSAPP_TOKEN')
        self.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        self.is_configured = bool(self.token and self.phone_number_id)

    def _send_template(self, to_number, template_name, components):
        if not self.is_configured:
            print(f"\n[WHATSAPP BOT ESTÉTICA] Mensaje a {to_number}: Plantilla {template_name}\nVariables: {components}\n")
            return True
        # Real send omitted for brevity
        return True

def notificar_reserva_estetica_creada(usuario, reserva):
    client = WhatsAppClient()
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": reserva.servicio.nombre},
            {"type": "text", "text": reserva.hora_inicio.strftime('%H:%M')}
        ]
    }]
    client._send_template(usuario.telefono or "1100000000", "reserva_confirmada_estetica", components)
