from django.utils import timezone
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from .models import TransaccionBancaria
from datetime import datetime

class WebhookThrottle(ScopedRateThrottle):
    scope = 'webhook'

class MercadoPagoWebhookView(APIView):
    throttle_classes = [WebhookThrottle]
    authentication_classes = [] # No requiere auth para el webhook
    permission_classes = []

    def post(self, request, *args, **kwargs):
        topic = request.query_params.get("topic") or request.data.get("type")
        
        # Atender los eventos de 'payment' (pagos de Mercado Pago)
        if topic == "payment":
            payment_id = request.query_params.get("id") or request.data.get("data", {}).get("id")
            
            if not payment_id:
                return Response({"status": "ignored"}, status=status.HTTP_200_OK)

            # Consultar a Mercado Pago para verificar la información (seguridad)
            # En producción se debe usar el ACCESS_TOKEN real
            mp_token = getattr(settings, 'MP_ACCESS_TOKEN', None)
            
            if mp_token:
                headers = {"Authorization": f"Bearer {mp_token}"}
                mp_response = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
                
                if mp_response.status_code == 200:
                    payment_data = mp_response.json()
                    
                    if payment_data.get("status") == "approved":
                        # Convertimos la fecha
                        fecha_aprobacion = datetime.fromisoformat(payment_data.get("date_approved"))
                        monto = payment_data.get("transaction_amount")
                        
                        TransaccionBancaria.objects.get_or_create(
                            mp_payment_id=str(payment_id),
                            defaults={
                                'monto': monto,
                                'fecha_acreditacion': fecha_aprobacion,
                                'estado': 'DISPONIBLE',
                                'datos_raw': payment_data
                            }
                        )
            else:
                # Si no hay token de MP configurado (entorno de pruebas local)
                # Simulamos la ingesta para poder probar la funcionalidad
                TransaccionBancaria.objects.get_or_create(
                    mp_payment_id=str(payment_id),
                    defaults={
                        'monto': request.data.get('transaction_amount', 0),
                        'fecha_acreditacion': timezone.now(),
                        'estado': 'DISPONIBLE',
                        'datos_raw': request.data
                    }
                )

        # Siempre devolver 200 OK para que MP no reenvíe
        return Response({"status": "received"}, status=status.HTTP_200_OK)
