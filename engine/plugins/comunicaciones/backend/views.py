import json
import logging
import os
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .whatsapp_service import WhatsAppClient

logger = logging.getLogger(__name__)

class WhatsAppWebhookView(APIView):
    permission_classes = [AllowAny] # Meta servers need access without our JWT

    def get(self, request):
        '''Meta Cloud API webhook verification'''
        verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'fireseed_violett_token')
        
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == verify_token:
                logger.info("[WHATSAPP WEBHOOK] Verified successfully.")
                return HttpResponse(challenge, status=200)
            else:
                return HttpResponse('Invalid verification token', status=403)
        return HttpResponse('Hello from WhatsApp Webhook', status=200)

    def post(self, request):
        '''Receive messages from Meta Cloud API'''
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        # Log the incoming message for debugging
        logger.debug(f"[WHATSAPP INCOMING] {body}")
        print(f"\\n[WHATSAPP RECIBIDO]: {json.dumps(body, indent=2)}\\n")
        
        if body.get('object') == 'whatsapp_business_account':
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    for msg in messages:
                        phone_number = msg.get('from')
                        msg_type = msg.get('type')
                        
                        client = WhatsAppClient()
                        
                        if msg_type == 'image':
                            # Usuario envió un comprobante de transferencia
                            image_id = msg.get('image', {}).get('id')
                            logger.info(f"[WHATSAPP] Comprobante de pago recibido de {phone_number}. Image ID: {image_id}")
                            
                            # Auto-respuesta
                            components = [{
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": "¡Gracias! Hemos recibido tu comprobante de pago."}
                                ]
                            }]
                            # Usaremos una plantilla generica o enviamos un texto directo.
                            # Para texto directo, Meta API usa un formato diferente, pero vamos a usar un metodo nuevo de texto directo.
                            client.send_text_message(phone_number, "¡Hola! Recibimos tu comprobante de pago. Nuestro equipo lo verificará a la brevedad y te confirmaremos la acreditación en tu perfil.")
                            
                        elif msg_type == 'text':
                            text_body = msg.get('text', {}).get('body', '')
                            logger.info(f"[WHATSAPP] Texto recibido de {phone_number}: {text_body}")
                            # Auto-respuesta básica
                            client.send_text_message(phone_number, "¡Hola! Soy el asistente virtual de Violett Pilates. Si enviaste un comprobante de transferencia, lo procesaremos pronto. Para consultas, aguarda a que un humano te responda.")
                            
            return HttpResponse('EVENT_RECEIVED', status=200)
            
        return HttpResponse(status=404)
