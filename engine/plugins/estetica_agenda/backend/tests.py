import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Usuario
from plugins.estetica_servicios.backend.models import ServicioEstetica
from plugins.estetica_paquetes.backend.models import BilleteraCliente
from plugins.estetica_agenda.backend.models import DisponibilidadDia, ReservaEstetica


class EsteticaAgendaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create(
            email='admin@estetica.com',
            nombre='Admin',
            apellido='Violett',
            rol='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        self.paciente = Usuario.objects.create(
            email='paciente@estetica.com',
            nombre='Lucia',
            apellido='Gomez',
            rol='CLIENTE'
        )
        self.servicio = ServicioEstetica.objects.create(
            nombre='Limpieza Facial Profunda',
            descripcion='Tratamiento facial',
            duracion_minutos=60,
            precio_base=25000,
            is_active=True
        )
        # Configurar disponibilidad todos los días de 09:00 a 13:00
        for dia in range(7):
            DisponibilidadDia.objects.create(
                dia_semana=dia,
                is_active=True,
                hora_apertura=datetime.time(9, 0),
                hora_cierre=datetime.time(13, 0)
            )
        self.manana = timezone.now().date() + datetime.timedelta(days=1)

    def test_booking_calculates_hora_fin_and_blocks_slot(self):
        billetera = BilleteraCliente.objects.create(
            usuario=self.paciente,
            servicio=self.servicio,
            sesiones_totales=2,
            sesiones_restantes=1,
            fecha_compra=timezone.now().date(),
            fecha_vencimiento=timezone.now().date() + datetime.timedelta(days=30),
            estado='ACTIVO'
        )
        self.client.force_authenticate(user=self.paciente)

        # Enviar hora_fin="00:00:00" como hacía BookingFunnel originalmente
        res = self.client.post('/api/estetica-turnos/', {
            'servicio': str(self.servicio.id),
            'fecha': self.manana.isoformat(),
            'hora_inicio': '10:00',
            'hora_fin': '00:00:00'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['hora_fin'], '11:00:00')

        billetera.refresh_from_db()
        self.assertEqual(billetera.sesiones_restantes, 0)
        self.assertEqual(billetera.estado, 'AGOTADO')

        # Verificar que 10:00 ya no aparece disponible en /api/disponibilidad/
        disp = self.client.get(f'/api/disponibilidad/?fecha={self.manana.isoformat()}&servicio_id={self.servicio.id}')
        self.assertEqual(disp.status_code, 200)
        self.assertNotIn('10:00', disp.data)
        self.assertIn('09:00', disp.data)
        self.assertIn('11:00', disp.data)

    def test_cancel_refunds_credit_and_reactivates_wallet(self):
        billetera = BilleteraCliente.objects.create(
            usuario=self.paciente,
            servicio=self.servicio,
            sesiones_totales=1,
            sesiones_restantes=0,
            fecha_compra=timezone.now().date(),
            fecha_vencimiento=timezone.now().date() + datetime.timedelta(days=30),
            estado='AGOTADO'
        )
        reserva = ReservaEstetica.objects.create(
            usuario=self.paciente,
            servicio=self.servicio,
            fecha=self.manana,
            hora_inicio=datetime.time(10, 0),
            hora_fin=datetime.time(11, 0),
            estado='CONFIRMADA'
        )
        self.client.force_authenticate(user=self.paciente)
        res = self.client.post(f'/api/estetica-turnos/{reserva.id}/cancelar/', {'devolver_credito': True}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['credito_devuelto'])

        billetera.refresh_from_db()
        self.assertEqual(billetera.sesiones_restantes, 1)
        self.assertEqual(billetera.estado, 'ACTIVO')

    def test_reschedule_updates_time_and_checks_overlap(self):
        reserva1 = ReservaEstetica.objects.create(
            usuario=self.paciente,
            servicio=self.servicio,
            fecha=self.manana,
            hora_inicio=datetime.time(9, 0),
            hora_fin=datetime.time(10, 0),
            estado='CONFIRMADA'
        )
        ReservaEstetica.objects.create(
            usuario=self.admin,
            servicio=self.servicio,
            fecha=self.manana,
            hora_inicio=datetime.time(11, 0),
            hora_fin=datetime.time(12, 0),
            estado='CONFIRMADA'
        )
        self.client.force_authenticate(user=self.paciente)

        # Intentar reprogramar al horario ocupado (11:00) debe fallar
        res_conflict = self.client.post(f'/api/estetica-turnos/{reserva1.id}/reprogramar/', {
            'fecha': self.manana.isoformat(),
            'hora_inicio': '11:00'
        }, format='json')
        self.assertEqual(res_conflict.status_code, 400)

        # Reprogramar a horario libre (10:00) debe funcionar
        res_ok = self.client.post(f'/api/estetica-turnos/{reserva1.id}/reprogramar/', {
            'fecha': self.manana.isoformat(),
            'hora_inicio': '10:00'
        }, format='json')
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(res_ok.data['hora_inicio'], '10:00:00')
        self.assertEqual(res_ok.data['hora_fin'], '11:00:00')

    def test_admin_manual_booking_and_wallet_sync(self):
        self.client.force_authenticate(user=self.admin)

        # Admin agenda turno manual sin descontar crédito
        res = self.client.post('/api/estetica-turnos/', {
            'usuario': str(self.paciente.id),
            'servicio': str(self.servicio.id),
            'fecha': self.manana.isoformat(),
            'hora_inicio': '12:00',
            'descontar_credito': False
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(res.data['usuario']), str(self.paciente.id))
        self.assertEqual(res.data['hora_fin'], '13:00:00')
