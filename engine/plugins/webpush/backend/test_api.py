
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from plugins.webpush.backend.models import PushSubscription

User = get_user_model()

class WebPushEndpointTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testapi@violett.com', password='password123', nombre='ApiUser', apellido='Test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_subscribe_endpoint(self):
        payload = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/fake123',
            'keys': {
                'p256dh': 'p256dh_key_base64',
                'auth': 'auth_key_base64'
            }
        }
        
        response = self.client.post('/api/webpush/subscribe/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify db
        sub = PushSubscription.objects.get(usuario=self.user)
        self.assertEqual(sub.endpoint, 'https://fcm.googleapis.com/fcm/send/fake123')
        self.assertEqual(sub.p256dh, 'p256dh_key_base64')
        self.assertEqual(sub.auth, 'auth_key_base64')
