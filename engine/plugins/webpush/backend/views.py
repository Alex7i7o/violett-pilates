from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PushSubscription

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