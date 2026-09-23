from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.utils import timezone
from core.models import Usuario, Turno, Clase, PlantillaTurno
import datetime

class PilatesApiTests(APITestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(email='test@test.com', password='pwd', rol='CLIENTE')
        self.clase = Clase.objects.create(nombre='Pilates Reformer', cupo_maximo=5)
        
        now = timezone.now()
        target_datetime = now + datetime.timedelta(days=2)
        
        self.turno = Turno.objects.create(
            clase=self.clase,
            fecha=target_datetime.date(),
            hora_inicio=target_datetime.time(),
            hora_fin=(target_datetime + datetime.timedelta(hours=1)).time(),
            cupo_actual=self.clase.cupo_maximo,
            estado='PROGRAMADO'
        )

    def test_auth_login(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'pwd'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
        
        # Test profile fetch
        profile_response = self.client.get('/api/client/profile/')
        self.assertEqual(profile_response.status_code, 200)

    def test_book_class(self):
        # Login
        login_res = self.client.post('/api/auth/login/', {'email': 'test@test.com', 'password': 'pwd'})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_res.data['access'])
        
        response = self.client.post('/api/reservas/book/', {
            'turno_id': str(self.turno.id),
            'recurring': False
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify slot decreased
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.cupo_actual, 4)

    def test_cancel_class(self):
        login_res = self.client.post('/api/auth/login/', {'email': 'test@test.com', 'password': 'pwd'})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_res.data['access'])
        
        # Book
        self.client.post('/api/reservas/book/', {'turno_id': str(self.turno.id), 'recurring': False})
        
        # Cancel
        response = self.client.post('/api/reservas/cancel/', {'turno_id': str(self.turno.id)})
        self.assertEqual(response.status_code, 200)
        
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.cupo_actual, 5) # Slot returns
