from django.core.management.base import BaseCommand
from core.models import Usuario, Clase, PlantillaTurno, Turno
from plugins.membresias.backend.models import Suscripcion, Plan
from django.utils import timezone
from datetime import timedelta, time

class Command(BaseCommand):
    help = 'Seeds data for Deep E2E tests'

    def handle(self, *args, **kwargs):
        admin, _ = Usuario.objects.get_or_create(email='admin@violett.com', defaults={'rol':'ADMIN', 'nombre':'Admin', 'is_staff':True})
        admin.set_password('password123')
        admin.save()
        
        profesor, _ = Usuario.objects.get_or_create(email='profesor@violett.com', defaults={'rol':'PROFESOR', 'nombre':'Profe'})
        profesor.set_password('password123')
        profesor.save()
        
        alumno, _ = Usuario.objects.get_or_create(email='alumno@violett.com', defaults={'rol':'CLIENTE', 'nombre':'Alumno'})
        alumno.set_password('password123')
        alumno.save()

        clase, _ = Clase.objects.get_or_create(nombre='Pilates Deep Test', defaults={'descripcion': 'Test'})
        
        now = timezone.now()
        hora_inicio = (now + timedelta(hours=1)).time()
        hora_fin = (now + timedelta(hours=2)).time()
        
        plantilla, _ = PlantillaTurno.objects.get_or_create(
            clase=clase,
            dia_semana=2, # Miercoles
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            defaults={'is_active': True}
        )
        
        Turno.objects.get_or_create(
            plantilla=plantilla,
            fecha=now.date(),
            defaults={
                'clase': clase,
                'hora_inicio': hora_inicio,
                'hora_fin': hora_fin
            }
        )
        
        plan, _ = Plan.objects.get_or_create(nombre='Plan Deep Test', defaults={'creditos': 10, 'dias_duracion': 30, 'precio': 1000})
        
        Suscripcion.objects.filter(usuario=alumno).delete()
        Suscripcion.objects.create(
            usuario=alumno,
            plan=plan,
            clases_totales=10,
            clases_disponibles=10,
            fecha_inicio=now.date(),
            fecha_fin=(now + timedelta(days=30)).date(),
            activa=True
        )
        
        self.stdout.write(self.style.SUCCESS('Deep test seed completed!'))
