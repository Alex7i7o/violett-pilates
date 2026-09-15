from django.core.management.base import BaseCommand
from core.models import Usuario

class Command(BaseCommand):
    help = 'Seeds the database with test users for E2E tests'

    def handle(self, *args, **kwargs):
        users = [
            {'email': 'admin@violett.com', 'rol': 'ADMIN', 'nombre': 'Admin', 'apellido': 'Test', 'is_staff': True, 'is_superuser': True},
            {'email': 'profesor@violett.com', 'rol': 'PROFESOR', 'nombre': 'Profesor', 'apellido': 'Test'},
            {'email': 'alumno@violett.com', 'rol': 'CLIENTE', 'nombre': 'Alumno', 'apellido': 'Test'}
        ]
        
        for u_data in users:
            email = u_data.pop('email')
            if not Usuario.objects.filter(email=email).exists():
                Usuario.objects.create_user(email=email, password='password123', **u_data)
                self.stdout.write(self.style.SUCCESS(f'Created user: {email}'))
            else:
                self.stdout.write(f'User already exists: {email}')
                user = Usuario.objects.get(email=email)
                user.set_password('password123')
                user.rol = u_data['rol']
                if u_data.get('is_staff'):
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
