from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PushSubscription
from .services import send_webpush
import threading
import time

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return Response({'detail': 'Invalid subscription data'}, status=400)

        # Create or update subscription
        sub, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'usuario': request.user,
                'p256dh': p256dh,
                'auth': auth
            }
        )
        return Response({'detail': 'Subscription saved', 'created': created})

class TestWebPushView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # We run it in a background thread with small delays to simulate multiple notifications arriving
        def send_sequence():
            time.sleep(1)
            send_webpush(
                request.user, 
                "¡Bienvenida a Violett!", 
                "Estamos felices de tenerte. Entrá a ver tus clases.", 
                {"url": "/"}
            )
            time.sleep(3)
            send_webpush(
                request.user, 
                "¡Cupo disponible!", 
                "Se liberó un lugar en Pilates Reformer hoy a las 18:00 hs.", 
                {"url": "/reservas"}
            )
            time.sleep(3)
            send_webpush(
                request.user, 
                "Recordatorio de clase", 
                "Te esperamos mañana para tu clase a las 09:00 hs.", 
                {"url": "/perfil"}
            )
            
        threading.Thread(target=send_sequence, daemon=True).start()
        return Response({'detail': 'Sequence started'})
