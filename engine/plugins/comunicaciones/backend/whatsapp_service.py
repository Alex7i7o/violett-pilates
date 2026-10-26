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

    def _send_template(self, to_number, template_name, components, language_code="es_AR"):
        if not self.is_configured:
            print(f"\n[WHATSAPP SIMULATOR] Plantilla '{template_name}' a {to_number} (Variables: {components})\n", flush=True)
            from backend_core.hooks import registry
            registry.execute('wpp_enviado_tracker', {})
            return True

        if not to_number:
            print("[WHATSAPP ERROR] to_number vacío para plantilla", flush=True)
            return False
            
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
                    "code": language_code
                },
                "components": components
            }
        }
        
        try:
            print(f"[WHATSAPP ENVIANDO PLANTILLA] '{template_name}' (Lang: {language_code}) a {phone}", flush=True)
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f"[WHATSAPP PLANTILLA ENVIADA EXITOSAMENTE] Status: {response.status_code} a {phone}", flush=True)
                from backend_core.hooks import registry
                registry.execute('wpp_enviado_tracker', {})
                return True
            else:
                if language_code == "es_AR" and "language" in response.text.lower():
                    print("[WHATSAPP PLANTILLA] Idioma es_AR no disponible. Reintentando con 'es'...", flush=True)
                    payload["template"]["language"]["code"] = "es"
                    res2 = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
                    if res2.status_code in [200, 201]:
                        print(f"[WHATSAPP PLANTILLA ENVIADA CON 'es'] Status: {res2.status_code}", flush=True)
                        from backend_core.hooks import registry
                        registry.execute('wpp_enviado_tracker', {})
                        return True

                print(f"[WHATSAPP ERROR META PLANTILLA] Status: {response.status_code} | Respuesta: {response.text}", flush=True)
                logger.error(f"[WHATSAPP ERROR] {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[WHATSAPP EXCEPTION PLANTILLA] {e}", flush=True)
            logger.error(f"[WHATSAPP EXCEPTION] {e}")
            return False

    def download_media_bytes(self, media_id: str):
        """Descarga el binario de una imagen o documento desde Meta WhatsApp Cloud API"""
        if not self.is_configured or not media_id:
            return None
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            res = requests.get(f"https://graph.facebook.com/v19.0/{media_id}", headers=headers, timeout=10)
            if res.status_code != 200:
                logger.error(f"[WHATSAPP MEDIA URL ERROR] {res.status_code} - {res.text}")
                return None
            media_url = res.json().get('url')
            if not media_url:
                return None
            file_res = requests.get(media_url, headers=headers, timeout=15)
            if file_res.status_code == 200:
                return file_res.content
            logger.error(f"[WHATSAPP MEDIA DOWNLOAD ERROR] {file_res.status_code}")
            return None
        except Exception as e:
            logger.error(f"[WHATSAPP MEDIA EXCEPTION] {e}")
            return None

    def send_text_message(self, to_number, text_message):
        '''Envia un mensaje de texto libre (solo funciona dentro de la ventana de 24hs iniciada por el usuario)'''
        try:
            from plugins.asistente.backend.services.formatter import sanitizar_para_whatsapp
            text_message = sanitizar_para_whatsapp(text_message)
        except Exception:
            pass
        if not self.is_configured:
            print(f"\n[WHATSAPP NO CONFIGURADO / SIMULADOR] (WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID vacios en el contenedor)", flush=True)
            print(f"-> Destino: {to_number}", flush=True)
            print(f"-> Mensaje: {text_message}\n", flush=True)
            from backend_core.hooks import registry
            registry.execute('wpp_enviado_tracker', {})
            return True

        if not to_number:
            print("[WHATSAPP ERROR] to_number vacio", flush=True)
            return False

        phone = str(to_number).replace('+', '').replace('-', '').replace(' ', '')

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': phone,
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': text_message
            }
        }

        try:
            print(f'[WHATSAPP ENVIANDO A META] URL: {self.base_url} | Destino: {phone}', flush=True)
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f'[WHATSAPP ENVIADO EXITOSAMENTE] Status: {response.status_code} | Respuesta: {response.text}', flush=True)
                from backend_core.hooks import registry
                registry.execute('wpp_enviado_tracker', {})
                return True
            else:
                print(f'[WHATSAPP ERROR META] Status: {response.status_code} | Respuesta: {response.text}', flush=True)
                logger.error(f'[WHATSAPP TEXT ERROR] {response.status_code} - {response.text}')
                return False
        except Exception as e:
            print(f'[WHATSAPP EXCEPTION] {e}', flush=True)
            logger.error(f'[WHATSAPP TEXT EXCEPTION] {e}')
            return False
def notificar_cancelacion_clase(usuario, turno):
    client = WhatsAppClient()
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": f"{turno.clase.nombre} ({turno.fecha})"},
            {"type": "text", "text": "El crédito ha sido devuelto a tu plan."}
        ]
    }]
    client._send_template(usuario.telefono or "1164142172", "clase_cancelada_admin", components)

def notificar_reserva_creada(usuario, turno):
    client = WhatsAppClient()
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": turno.clase.nombre},
            {"type": "text", "text": turno.hora_inicio.strftime('%H:%M')}
        ]
    }]
    client._send_template(usuario.telefono or "1164142172", "reserva_confirmada", components)

def notificar_cancelacion_usuario(usuario, turno):
    client = WhatsAppClient()
    components = [{
        "type": "body",
        "parameters": [
            {"type": "text", "text": usuario.nombre},
            {"type": "text", "text": f"{turno.clase.nombre} el {turno.fecha}"}
        ]
    }]
    client._send_template(usuario.telefono or "1164142172", "reserva_cancelada_usuario", components)
