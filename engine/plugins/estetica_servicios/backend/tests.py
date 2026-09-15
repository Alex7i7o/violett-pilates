from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import ServicioEstetica

User = get_user_model()

class ServicioEsteticaTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@violett.com',
            password='password123',
            nombre='Admin',
            apellido='Test'
        )
        self.cliente = User.objects.create_user(
            email='cliente@violett.com',
            password='password123',
            nombre='Cliente',
            apellido='Test',
            rol='CLIENTE'
        )
        self.servicio = ServicioEstetica.objects.create(
            nombre='Limpieza Facial',
            descripcion='Limpieza profunda',
            duracion_minutos=60
        )

    def test_list_servicios_public(self):
        # AllowAny should let unauthorized users list
        response = self.client.get('/api/servicios/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_servicio_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'nombre': 'Masaje Relajante',
            'descripcion': 'Masaje 60 min',
            'duracion_minutos': 60
        }
        response = self.client.post('/api/servicios/', data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ServicioEstetica.objects.count(), 2)

    def test_create_servicio_cliente_forbidden(self):
        self.client.force_authenticate(user=self.cliente)
        data = {
            'nombre': 'Hack',
            'duracion_minutos': 30
        }
        response = self.client.post('/api/servicios/', data)
        self.assertEqual(response.status_code, 403)
