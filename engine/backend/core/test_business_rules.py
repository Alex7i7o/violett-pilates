from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
import datetime
from core.models import Usuario, Clase, Turno, Reserva
from core.services import cancelar_reserva
from plugins.automatizaciones.backend.management.commands.cancel_empty_classes import Command as EvaluatorCommand

class BusinessRulesTestCase(TestCase):
    def setUp(self):
        self.user1 = Usuario.objects.create_user(email='user1@test.com', password='pwd', rol='CLIENTE', nombre='U1', apellido='A')
        self.user2 = Usuario.objects.create_user(email='user2@test.com', password='pwd', rol='CLIENTE', nombre='U2', apellido='A')
        self.user3 = Usuario.objects.create_user(email='user3@test.com', password='pwd', rol='CLIENTE', nombre='U3', apellido='A')
        
        self.clase = Clase.objects.create(nombre='Pilates Reformer', cupo_maximo=3)

    def create_turno_for_hours_ahead(self, hours):
        now = timezone.now()
        target_datetime = now + datetime.timedelta(hours=hours)
        fecha = target_datetime.date()
        hora_inicio = target_datetime.time()
        # Mock the time carefully
        turno = Turno.objects.create(
            clase=self.clase,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=(target_datetime + datetime.timedelta(hours=1)).time(),
            cupo_actual=self.clase.cupo_maximo,
            estado='PROGRAMADO',
            evaluado_25hs=False
        )
        return turno

    def book(self, user, turno):
        reserva = Reserva.objects.create(usuario=user, turno=turno, estado='CONFIRMADA')
        turno.cupo_actual -= 1
        turno.save()
        return reserva

    @patch('core.services.get_plugin_config')
    def test_cancelacion_temprana(self, mock_config):
        # Configuramos limite en 24hs
        mock_config.return_value = {'horas_limite_cancelacion': 24}
        
        turno = self.create_turno_for_hours_ahead(26) # 26hs from now > 24hs
        self.book(self.user1, turno)
        
        exito, msg = cancelar_reserva(turno.id, self.user1)
        self.assertTrue(exito)
        
        reserva = Reserva.objects.get(turno=turno, usuario=self.user1)
        self.assertEqual(reserva.estado, 'CANCELADA') # Early
        self.assertEqual(turno.cupo_actual, 3) # Slot freed

    @patch('core.services.get_plugin_config')
    def test_cancelacion_tardia(self, mock_config):
        mock_config.return_value = {'horas_limite_cancelacion': 24}
        
        turno = self.create_turno_for_hours_ahead(23) # 23hs from now < 24hs
        self.book(self.user1, turno)
        
        exito, msg = cancelar_reserva(turno.id, self.user1)
        self.assertTrue(exito)
        
        reserva = Reserva.objects.get(turno=turno, usuario=self.user1)
        self.assertEqual(reserva.estado, 'CANCELADA_TARDIA') # Tardy
        self.assertEqual(turno.cupo_actual, 3) # Slot freed

    @patch('plugins.automatizaciones.backend.management.commands.cancel_empty_classes.get_plugin_config')
    def test_evaluator_scenario_a_low_attendance(self, mock_config):
        mock_config.return_value = {
            'cancel_empty_classes': {
                'enabled': True,
                'min_students': 2,
                'hours_before_class': 25
            }
        }
        
        # 24.5 hours ahead matches 0 < time_diff <= 25
        turno = self.create_turno_for_hours_ahead(24.5)
        self.book(self.user1, turno) # Only 1 student (< 2)
        
        evaluator = EvaluatorCommand()
        evaluator.handle()
        
        turno.refresh_from_db()
        self.assertEqual(turno.estado, 'CANCELADO')
        self.assertTrue(turno.evaluado_25hs)
        
        reserva = Reserva.objects.get(turno=turno, usuario=self.user1)
        self.assertEqual(reserva.estado, 'CANCELADA')

    @patch('plugins.automatizaciones.backend.management.commands.cancel_empty_classes.get_plugin_config')
    def test_evaluator_scenario_b_exact_minimum_with_available_slots(self, mock_config):
        mock_config.return_value = {
            'cancel_empty_classes': {
                'enabled': True,
                'min_students': 2,
                'hours_before_class': 25
            }
        }
        
        turno = self.create_turno_for_hours_ahead(24.5)
        self.book(self.user1, turno)
        self.book(self.user2, turno)
        # 2 students == 2 min_students. Max is 3, so slot available!
        
        evaluator = EvaluatorCommand()
        evaluator.handle()
        
        turno.refresh_from_db()
        self.assertEqual(turno.estado, 'PROGRAMADO')
        self.assertTrue(turno.evaluado_25hs)

    @patch('plugins.automatizaciones.backend.management.commands.cancel_empty_classes.get_plugin_config')
    def test_evaluator_scenario_c_full_class(self, mock_config):
        mock_config.return_value = {
            'cancel_empty_classes': {
                'enabled': True,
                'min_students': 2,
                'hours_before_class': 25
            }
        }
        
        turno = self.create_turno_for_hours_ahead(24.5)
        self.book(self.user1, turno)
        self.book(self.user2, turno)
        self.book(self.user3, turno)
        # 3 students. Full class.
        
        evaluator = EvaluatorCommand()
        evaluator.handle()
        
        turno.refresh_from_db()
        self.assertEqual(turno.estado, 'PROGRAMADO')
        self.assertTrue(turno.evaluado_25hs)

