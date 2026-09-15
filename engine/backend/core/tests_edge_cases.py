from django.test import TestCase
from django.utils import timezone
from .models import Usuario, Turno, Reserva, Clase
from core.services import process_booking
import datetime
import threading

class ConcurrencyEdgeCaseTests(TestCase):
    def setUp(self):
        self.u1 = Usuario.objects.create_user(email='u1@test.com', password='pwd', nombre='u1', apellido='u1', rol='CLIENTE')
        self.u2 = Usuario.objects.create_user(email='u2@test.com', password='pwd', nombre='u2', apellido='u2', rol='CLIENTE')
        self.clase = Clase.objects.create(nombre='Pilates', descripcion='', cupo_maximo=1) # SÓLO 1 CUPO
        
        # Turno mañana
        self.turno = Turno.objects.create(
            clase=self.clase,
            fecha=timezone.localdate() + datetime.timedelta(days=1),
            hora_inicio=datetime.time(10, 0),
            hora_fin=datetime.time(11, 0),
            estado='PROGRAMADO'
        )
        
        # Simular que tienen membresia
        from plugins.membresias.backend.models import Suscripcion, Plan
        self.plan = Plan.objects.create(nombre='P1', cantidad_clases=10, precio=100)
        Suscripcion.objects.create(usuario=self.u1, plan=self.plan, clases_restantes=10, fecha_inicio=timezone.localdate(), fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30), estado='ACTIVO')
        Suscripcion.objects.create(usuario=self.u2, plan=self.plan, clases_restantes=10, fecha_inicio=timezone.localdate(), fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30), estado='ACTIVO')

    def test_overbooking_prevention(self):
        """Si dos usuarias intentan reservar el último cupo al mismo tiempo, solo una debe pasar."""
        results = []
        
        self.turno.cupo_actual = 1
        self.turno.save()

        def book(user):
            try:
                self.turno.refresh_from_db()
                print(f"Cupo before {user.nombre} booking: {self.turno.cupo_actual}")
                success, msg = process_booking(str(self.turno.id), user)
                results.append({'success': success, 'detail': msg})
                print(f"User {user.nombre} booking result: {success}, {msg}")
            except Exception as e:
                results.append({'success': False, 'detail': str(e)})

        # Ejecutamos secuencialmente porque el test runner de django no se lleva bien con threads concurrentes usando DB en sqlite :memory:
        book(self.u1)
        book(self.u2)
        
        successes = [r for r in results if r.get('success')]
        self.assertEqual(len(successes), 1, "Sólo una reserva debió ser exitosa si había 1 solo cupo.")
        self.assertEqual(Reserva.objects.filter(turno=self.turno).count(), 1)
        
    def test_booking_expired_subscription(self):
        """No se debe poder reservar si no hay membresía activa."""
        self.turno.cupo_actual = 1
        self.turno.save()
        u_no_sub = Usuario.objects.create_user(email='u3@test.com', password='pwd', nombre='u3', apellido='u3', rol='CLIENTE')
        success, msg = process_booking(str(self.turno.id), u_no_sub)
        print(f"Expired sub test result: {success}, {msg}")
        self.assertFalse(success)
        self.assertIn("No tienes un plan activo", msg)

