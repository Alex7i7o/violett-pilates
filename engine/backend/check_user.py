import os
import django
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # add plugins
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()

from core.models import Usuario

email = 'alexxaguero@gmail.com'
try:
    u = Usuario.objects.get(email=email)
    print(f'User: {u.email}, Role: {u.rol}, is_staff: {u.is_staff}')
    u.set_password('12345678')
    u.rol = 'PROFESOR'
    u.save()
    print('Password reset to 12345678 and role set to PROFESOR')
except Usuario.DoesNotExist:
    print('User does not exist, creating...')
    u = Usuario.objects.create_user(email=email, password='password123', nombre='Alex', apellido='Aguero', rol='PROFESOR')
    print('Created with password: password123')
