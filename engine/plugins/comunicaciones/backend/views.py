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
        
        print(f"[WHATSAPP WEBHOOK GET] mode={mode}, token={token}", flush=True)
        if mode and token:
            if mode == 'subscribe' and token == verify_token:
                logger.info("[WHATSAPP WEBHOOK] Verified successfully.")
                print("[WHATSAPP WEBHOOK] Verificado exitosamente con Meta (hub.challenge devuelto).", flush=True)
                return HttpResponse(challenge, status=200)
            else:
                print(f"[WHATSAPP WEBHOOK ERROR] Token no coincide: recibido='{token}', esperado='{verify_token}'", flush=True)
                return HttpResponse('Invalid verification token', status=403)
        return HttpResponse('Hello from WhatsApp Webhook', status=200)

    def post(self, request):
        '''Receive messages from Meta Cloud API'''
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            print("[WHATSAPP WEBHOOK ERROR] Payload recibido no es JSON valido", flush=True)
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        print(f"\n[WHATSAPP WEBHOOK POST RECIBIDO]:\n{json.dumps(body, indent=2)}\n", flush=True)
        
        if body.get('object') == 'whatsapp_business_account':
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Log de status updates (sent, delivered, read, failed)
                    statuses = value.get('statuses', [])
                    for st in statuses:
                        print(f"[WHATSAPP STATUS] Destino: {st.get('recipient_id')} | Estado: {st.get('status')} | Errores: {st.get('errors')}", flush=True)
                    
                    messages = value.get('messages', [])
                    
                    for msg in messages:
                        phone_number = msg.get('from')
                        msg_type = msg.get('type')
                        
                        client = WhatsAppClient()
                        
                        if msg_type == 'image':
                            image_id = msg.get('image', {}).get('id')
                            caption = msg.get('image', {}).get('caption', '')
                            logger.info(f"[WHATSAPP] Imagen recibida de {phone_number}. Image ID: {image_id}")
                            from backend_core.hooks import registry
                            registry.execute('whatsapp_imagen_recibida', {
                                'phone': phone_number,
                                'image_id': image_id,
                                'caption': caption,
                                'raw_msg': msg
                            })
                            if not registry.listeners.get('whatsapp_imagen_recibida'):
                                client.send_text_message(phone_number, "¡Hola! ✦ Recibimos tu comprobante de pago. Nuestro equipo lo verificará a la brevedad.")

                        elif msg_type in ['audio', 'voice']:
                            audio_obj = msg.get('audio') or msg.get('voice') or {}
                            audio_id = audio_obj.get('id')
                            mime_type = audio_obj.get('mime_type', 'audio/ogg')
                            logger.info(f"[WHATSAPP] Audio recibido de {phone_number}. Audio ID: {audio_id} (mime: {mime_type})")
                            from backend_core.hooks import registry
                            registry.execute('whatsapp_audio_recibido', {
                                'phone': phone_number,
                                'audio_id': audio_id,
                                'mime_type': mime_type,
                                'raw_msg': msg
                            })
                            if not registry.listeners.get('whatsapp_audio_recibido'):
                                client.send_text_message(phone_number, "¡Hola! ✦ Recibimos tu mensaje de audio. En breve te responderemos.")
                            
                        elif msg_type == 'text':
                            text_body = msg.get('text', {}).get('body', '')
                            logger.info(f"[WHATSAPP] Texto recibido de {phone_number}: {text_body}")
                            from backend_core.hooks import registry
                            # Emitir hook para el Asistente Multi-Agente
                            registry.execute('whatsapp_mensaje_recibido', {
                                'phone': phone_number,
                                'text': text_body,
                                'raw_msg': msg
                            })
                            # Fallback si el plugin asistente no esta activo
                            if not registry.listeners.get('whatsapp_mensaje_recibido'):
                                client.send_text_message(phone_number, "¡Hola! ✦ Gracias por comunicarte con nosotros. En breve una recepcionista te responderá.")
                            
            return HttpResponse('EVENT_RECEIVED', status=200)
            
        return HttpResponse(status=404)
