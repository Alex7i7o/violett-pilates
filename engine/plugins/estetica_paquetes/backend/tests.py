from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import ReglaPaquete, BilleteraCliente
from plugins.estetica_servicios.backend.models import ServicioEstetica

User = get_user_model()

class EsteticaPaquetesTests(APITestCase):
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
            nombre='Masaje',
            descripcion='Masaje',
            duracion_minutos=60
        )
        self.regla = ReglaPaquete.objects.create(
            cantidad_sesiones=5,
            descuento_porcentaje=10.0
        )
        self.billetera = BilleteraCliente.objects.create(
            usuario=self.cliente,
            servicio=self.servicio,
            sesiones_totales=5,
            sesiones_restantes=5,
            fecha_vencimiento=timezone.now().date() + timedelta(days=30)
        )

    def test_list_reglas_public(self):
        response = self.client.get('/api/reglas-paquetes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_billetera_access_cliente(self):
        self.client.force_authenticate(user=self.cliente)
        response = self.client.get('/api/billeteras/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sesiones_restantes'], 5)

    def test_billetera_access_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/billeteras/')
        self.assertEqual(response.status_code, 200)

    def test_admin_create_regla(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'cantidad_sesiones': 10,
            'descuento_porcentaje': '15.00'
        }
        response = self.client.post('/api/reglas-paquetes/', data)
        self.assertEqual(response.status_code, 201)
