from django.test import TestCase
from django.utils import timezone
from core.models import Usuario, Clase, Turno, PlantillaTurno, Reserva
from plugins.membresias.backend.models import Plan, Suscripcion
from plugins.profesores.backend.models import Profesor, PlantillaProfesor, TurnoProfesor
from core.services import generar_turnos_desde_plantillas, cancelar_reserva
import datetime

class CoreSaaSTestCase(TestCase):
    def setUp(self):
        # Crear usuarios
        self.admin = Usuario.objects.create_user(email="admin@test.com", password="pwd", rol="ADMIN", nombre="Ad", apellido="A")
        self.prof = Usuario.objects.create_user(email="prof@test.com", password="pwd", rol="PROFESOR", nombre="Pr", apellido="P")
        self.alumna = Usuario.objects.create_user(email="alum@test.com", password="pwd", rol="CLIENTE", nombre="Al", apellido="A")
        self.alumna_sin_plan = Usuario.objects.create_user(email="alum2@test.com", password="pwd", rol="CLIENTE", nombre="Al2", apellido="A2")
        
        # Crear profesor
        self.profesor_model = Profesor.objects.create(email="prof@test.com", nombre="Pr", apellido="P", usuario=self.prof)
        
        # Crear clase
        self.clase = Clase.objects.create(nombre="Pilates", cupo_maximo=2)
        
        # Crear plan y suscripcion
        self.plan = Plan.objects.create(nombre="Plan 8", cantidad_clases=8, is_active=True, precio=1000)
        self.suscripcion = Suscripcion.objects.create(
            usuario=self.alumna, plan=self.plan, clases_restantes=8,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
            estado="ACTIVO"
        )
        
        # Crear plantilla
        self.plantilla = PlantillaTurno.objects.create(
            clase=self.clase,
            dia_semana=timezone.localdate().isoweekday(),
            hora_inicio=datetime.time(10, 0),
            hora_fin=datetime.time(11, 0)
        )
        PlantillaProfesor.objects.create(plantilla=self.plantilla, profesor=self.profesor_model)

    def test_generacion_turnos_crons(self):
        # Test cron job
        generar_turnos_desde_plantillas()
        turnos = Turno.objects.all()
        self.assertGreater(turnos.count(), 0)
        
        # Check that TurnoProfesor was created
        turno = turnos.first()
        tp = TurnoProfesor.objects.filter(turno=turno).first()
        self.assertIsNotNone(tp)
        self.assertEqual(tp.profesor, self.profesor_model)

    def test_reserva_con_suscripcion(self):
        generar_turnos_desde_plantillas()
        turno = Turno.objects.filter(clase=self.clase).first()
        
        # Simulate book request by firing hooks
        from backend_core.hooks import registry
        data = {'success': True}
        registry.execute('pre_book_validation', data, user=self.alumna, turno=turno)
        self.assertTrue(data.get('success'))
        
        # Do the actual save like the view does
        reserva = Reserva.objects.create(turno=turno, usuario=self.alumna, estado='CONFIRMADA')
        registry.execute('post_book_action', {}, user=self.alumna, turno=turno, reserva=reserva)
        
        # Check deduction
        self.suscripcion.refresh_from_db()
        self.assertEqual(self.suscripcion.clases_restantes, 7)
        
    def test_reserva_sin_suscripcion(self):
        generar_turnos_desde_plantillas()
        turno = Turno.objects.filter(clase=self.clase).first()
        
        from backend_core.hooks import registry
        data = {'success': True}
        registry.execute('pre_book_validation', data, user=self.alumna_sin_plan, turno=turno)
        self.assertFalse(data.get('success'))
        self.assertIn("No tienes un plan activo", data.get('detail'))
        
    def test_cancelacion_reembolso(self):
        # Cancel > 12 hours before
        generar_turnos_desde_plantillas()
        turno = Turno.objects.first()
        turno.fecha = timezone.localdate() + datetime.timedelta(days=2) # far in future
        turno.save()
        
        reserva = Reserva.objects.create(turno=turno, usuario=self.alumna, estado='CONFIRMADA')
        from backend_core.hooks import registry
        registry.execute('post_book_action', {}, user=self.alumna, turno=turno, reserva=reserva)
        
        self.suscripcion.refresh_from_db()
        self.assertEqual(self.suscripcion.clases_restantes, 7)
        
        # Cancel
        exito, msg = cancelar_reserva(turno.id, self.alumna)
        self.assertTrue(exito)
        self.suscripcion.refresh_from_db()
        self.assertEqual(self.suscripcion.clases_restantes, 8) # refunded!
