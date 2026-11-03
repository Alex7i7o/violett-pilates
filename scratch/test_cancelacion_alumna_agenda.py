import os
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend_core.settings'

sys.path.insert(0, os.path.abspath('engine/backend'))
sys.path.insert(0, os.path.abspath('engine'))

import django
django.setup()

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import Usuario, Clase, Turno, Reserva
from plugins.membresias.backend.models import Plan, Suscripcion, ReservaMembresia
from core.serializers import AdminTurnoSerializer
from core.admin_views import AdminAgendaView
from plugins.asistente.backend.tools.turnos_tools import cancelar_reserva_alumna

print("=== Setting up test fixtures ===")
call_command('migrate', verbosity=0)

factory = APIRequestFactory()

admin_user = Usuario.objects.create_superuser(
    email='admin@violett.com',
    nombre='Admin',
    apellido='Violett',
    password='password123'
)

alex = Usuario.objects.create_user(
    email='alex@test.com',
    nombre='Alex',
    apellido='Aguero',
    telefono='1162051543',
    rol='CLIENTE'
)

plan = Plan.objects.create(nombre='Plan 4 Clases', cantidad_clases=4, precio=40000)
sub_alex = Suscripcion.objects.create(
    usuario=alex,
    plan=plan,
    clases_restantes=3,
    estado='ACTIVO',
    fecha_inicio=timezone.localdate(),
    fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30)
)

clase = Clase.objects.create(nombre='Pilates Reformer', duracion_minutos=60, cupo_maximo=3)

# Turno para este sábado a las 17:00 hs
fecha_sabado = timezone.localdate() + datetime.timedelta(days=4)
turno_sabado = Turno.objects.create(
    clase=clase,
    fecha=fecha_sabado,
    hora_inicio=datetime.time(17, 0),
    hora_fin=datetime.time(18, 0),
    cupo_actual=2,
    estado='PROGRAMADO'
)

# Reserva activa de Alex
reserva_alex = Reserva.objects.create(
    turno=turno_sabado,
    usuario=alex,
    estado='CONFIRMADA'
)
ReservaMembresia.objects.create(reserva=reserva_alex, suscripcion=sub_alex)

print("\n--- Verificación antes de cancelar ---")
ser_antes = AdminTurnoSerializer(turno_sabado).data
print(f"Reservas en turno antes: {len(ser_antes['reservas_list'])}")
assert len(ser_antes['reservas_list']) == 1
assert ser_antes['reservas_list'][0]['alumno_nombre'] == 'Alex'

print("\n--- TEST 1: Cancelación de reserva por el Asistente IA ---")
res_tool = cancelar_reserva_alumna.invoke({
    "usuario_id": str(alex.id),
    "fecha_o_dia": fecha_sabado.isoformat(),
    "hora_str": "17:00"
})
print(f"Respuesta de la tool: {res_tool}")

reserva_alex.refresh_from_db()
sub_alex.refresh_from_db()
turno_sabado.refresh_from_db()

# 1. Estado debe ser CANCELADA_TIEMPO
assert reserva_alex.estado == 'CANCELADA_TIEMPO', f"Esperado CANCELADA_TIEMPO, obtuvo {reserva_alex.estado}"
print(f"✓ Reserva actualizada a estado={reserva_alex.estado}")

# 2. Crédito reintegrado
assert sub_alex.clases_restantes == 4, f"Esperado 4 créditos, tiene {sub_alex.clases_restantes}"
print(f"✓ Crédito devuelto exitosamente: {sub_alex.clases_restantes} disponibles.")

# 3. Cupo de camilla liberado
assert turno_sabado.cupo_actual == 3, f"Esperado 3 camillas libres, tiene {turno_sabado.cupo_actual}"
print(f"✓ Camilla liberada: {turno_sabado.cupo_actual} libres.")

# 4. AdminTurnoSerializer NO debe incluir la reserva cancelada
ser_despues = AdminTurnoSerializer(turno_sabado).data
print(f"Reservas en turno después de cancelar: {len(ser_despues['reservas_list'])}")
assert len(ser_despues['reservas_list']) == 0, f"reservas_list debe estar vacía, pero tiene {len(ser_despues['reservas_list'])}"
print("✓ reservas_list está completamente vacía (no aparece como inscripta ni como ausente).")

print("\n--- TEST 2: AdminAgendaView respuesta para la Agenda ---")
agenda_view = AdminAgendaView.as_view()
req = factory.get(f'/api/admin/agenda/?fecha={fecha_sabado.isoformat()}')
force_authenticate(req, user=admin_user)
resp = agenda_view(req)
turno_data = next(t for t in resp.data if t['id'] == str(turno_sabado.id))
assert len(turno_data['reservas_list']) == 0
print(f"✓ En la Agenda del día {fecha_sabado.isoformat()}, el turno tiene 0 inscriptas y 3 libres.")

print("\n--- TEST 3: Compatibilidad con registros legacy estado='CANCELADA' ---")
marcela = Usuario.objects.create_user(
    email='marcela@test.com',
    nombre='Marcela',
    apellido='Gomez',
    rol='CLIENTE'
)
reserva_legacy = Reserva.objects.create(
    turno=turno_sabado,
    usuario=marcela,
    estado='CANCELADA'
)
ser_legacy = AdminTurnoSerializer(turno_sabado).data
assert len(ser_legacy['reservas_list']) == 0, "Registros legacy 'CANCELADA' tampoco deben aparecer en reservas_list"
print("✓ Registros con estado='CANCELADA' son excluidos al 100% de la Agenda.")

print("\n==========================================")
print("¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100%)!")
print("==========================================")
