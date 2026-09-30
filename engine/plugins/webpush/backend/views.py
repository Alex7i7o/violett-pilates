from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PushSubscription
from .services import send_webpush, send_webpush_sync
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

        # send_webpush is already non-blocking (runs in background thread)
        def send_welcome():
            time.sleep(2)
            send_webpush(
                request.user,
                "¡Avisos activados con éxito!",
                "Bienvenida. Por acá te vamos a avisar cuando se libere un lugar en una clase.",
                {"url": "/"}
            )
        threading.Thread(target=send_welcome, daemon=True).start()

        return Response({'detail': 'Subscription saved', 'created': created})


class TestWebPushView(APIView):
    """Diagnostic endpoint - runs synchronously so errors are visible in the response."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        success, message = send_webpush_sync(
            request.user,
            "¡Notificación de prueba!",
            "Si ves esto, las notificaciones push están funcionando correctamente.",
            {"url": "/"}
        )
        status_code = 200 if success else 500
        return Response({'success': success, 'detail': message}, status=status_code)
