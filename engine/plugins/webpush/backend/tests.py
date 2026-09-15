from django.test import TestCase
from django.contrib.auth import get_user_model
from plugins.webpush.backend.models import PushSubscription
from plugins.webpush.backend.services import send_webpush
from plugins.webpush.backend.hooks import on_reserva_creada
from core.models import Clase, Turno, Reserva
from datetime import date, time
from unittest.mock import patch

User = get_user_model()

class WebPushTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testpush@violett.com', password='password123', nombre='PushUser', apellido='Test')
        self.sub = PushSubscription.objects.create(
            usuario=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/xyz',
            p256dh='fake_p256dh',
            auth='fake_auth'
        )
        
        self.clase = Clase.objects.create(nombre='pilates', cupo_maximo=5)
        self.turno = Turno.objects.create(
            clase=self.clase,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0)
        )
        self.reserva = Reserva.objects.create(
            usuario=self.user,
            turno=self.turno
        )

    @patch('plugins.webpush.backend.services.logger.info')
    def test_send_webpush_simulator(self, mock_logger):
        send_webpush(self.user, 'Test Title', 'Test Body')
        self.assertTrue(mock_logger.called)
        # Check if the correct message was logged
        call_arg = mock_logger.call_args[0][0]
        self.assertIn('Sent push to testpush@violett.com', call_arg)
        self.assertIn('Test Title', call_arg)

    @patch('plugins.webpush.backend.hooks.send_webpush')
    def test_hook_reserva_creada(self, mock_send_webpush):
        # Trigger the hook manually as the core signal would
        on_reserva_creada(self.reserva)
        self.assertTrue(mock_send_webpush.called)
        
        args, kwargs = mock_send_webpush.call_args
        self.assertEqual(args[0], self.user)
        self.assertEqual(args[1], 'Reserva Confirmada')
        self.assertIn('Has reservado exitosamente', args[2])
