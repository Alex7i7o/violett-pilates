import logging
import os
import requests

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self):
        # En prod se leen de variables de entorno
        self.token = os.environ.get('WHATSAPP_TOKEN')
        self.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        self.is_configured = bool(self.token and self.phone_number_id)

    def _send_template(self, to_number, template_name, components):
        if not self.is_configured:
            logger.info(f"[WHATSAPP SIMULATOR] Mensaje a {to_number}: Plantilla {template_name} | Variables: {components}")
            print(f"\n[WHATSAPP SIMULATOR] Mensaje a {to_number}: Plantilla {template_name}\nVariables: {components}\n")
            return True

        if not to_number:
            return False
            
        # Limpiar el número (asumimos código de área internacional ya configurado o lo agregamos según país)
        phone = str(to_number).replace("+", "").replace("-", "").replace(" ", "")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "es_AR"
                },
                "components": components
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                logger.info(f"[WHATSAPP OK] Mensaje enviado a {phone}")
                return True
            else:
                logger.error(f"[WHATSAPP ERROR] {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"[WHATSAPP EXCEPTION] {e}")
            return False

def notificar_cancelacion_clase(usuario, turno):
    client = WhatsAppClient()
    # Plantilla de ejemplo: "Hola {{1}}, la clase de {{2}} fue cancelada. {{3}}"
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": f"{turno.clase.nombre} ({turno.fecha})"},
            {"type": "text", "text": "El crédito ha sido devuelto a tu plan."}
        ]
    }]
    client._send_template(usuario.telefono or "1100000000", "clase_cancelada_admin", components)

def notificar_reserva_creada(usuario, turno):
    client = WhatsAppClient()
    # Plantilla: "Hola {{1}}, tu reserva para {{2}} a las {{3}} está confirmada."
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": turno.clase.nombre},
            {"type": "text", "text": turno.hora_inicio.strftime('%H:%M')}
        ]
    }]
    client._send_template(usuario.telefono or "1100000000", "reserva_confirmada", components)

def notificar_cancelacion_usuario(usuario, turno):
    client = WhatsAppClient()
    # Plantilla: "Hola {{1}}, cancelaste tu turno de {{2}}."
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": f"{turno.clase.nombre} el {turno.fecha}"}
        ]
    }]
    client._send_template(usuario.telefono or "1100000000", "reserva_cancelada_usuario", components)
