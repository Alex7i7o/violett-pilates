from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date, time
from .models import DisponibilidadDia, ReservaEstetica
from plugins.estetica_servicios.backend.models import ServicioEstetica
from plugins.estetica_paquetes.backend.models import BilleteraCliente

User = get_user_model()

class EsteticaAgendaTests(APITestCase):
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
        self.disponibilidad = DisponibilidadDia.objects.create(
            dia_semana=0, # Monday
            hora_apertura=time(9, 0),
            hora_cierre=time(18, 0),
            is_active=True
        )
        self.billetera = BilleteraCliente.objects.create(
            usuario=self.cliente,
            servicio=self.servicio,
            sesiones_totales=5,
            sesiones_restantes=5,
            fecha_vencimiento=timezone.now().date() + timedelta(days=30),
            estado='ACTIVO'
        )

    def test_disponibilidad_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/config-dias/')
        self.assertEqual(response.status_code, 200)

    def test_get_disponibilidad_slots(self):
        fecha = '2024-01-01'
        response = self.client.get(f'/api/disponibilidad/?fecha={fecha}&servicio_id={self.servicio.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 8)
        self.assertIn('09:00', response.data)

    def test_crear_reserva_con_saldo(self):
        self.client.force_authenticate(user=self.cliente)
        data = {
            'servicio': str(self.servicio.id),
            'fecha': '2024-01-01',
            'hora_inicio': '09:00',
            'hora_fin': '10:00'
        }
        response = self.client.post('/api/estetica-turnos/', data)
        self.assertEqual(response.status_code, 201)
        
        self.billetera.refresh_from_db()
        self.assertEqual(self.billetera.sesiones_restantes, 4)

    def test_crear_reserva_sin_saldo(self):
        self.billetera.sesiones_restantes = 0
        self.billetera.estado = 'AGOTADO'
        self.billetera.save()

        self.client.force_authenticate(user=self.cliente)
        data = {
            'servicio': str(self.servicio.id),
            'fecha': '2024-01-01',
            'hora_inicio': '10:00',
            'hora_fin': '11:00'
        }
        response = self.client.post('/api/estetica-turnos/', data)
        self.assertEqual(response.status_code, 400)
