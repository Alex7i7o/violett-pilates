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
from core.models import Usuario, Clase, Turno, Reserva, PlantillaTurno
from plugins.membresias.backend.models import Plan, Suscripcion, ReservaMembresia
from plugins.asistente.backend.models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from core.admin_views import AdminTurnoViewSet, AdminAgendaView
from core.services import generar_turnos_desde_plantillas
from plugins.asistente.backend.tools.turnos_tools import consultar_turnos_disponibles

print("=== Setting up in-memory SQLite schema ===")
call_command('migrate', verbosity=0)

factory = APIRequestFactory()

# Create Admin User
admin_user = Usuario.objects.create_superuser(
    email='admin@violett.com',
    nombre='Admin',
    apellido='Violett',
    password='password123'
)

# Create Alumna Alex
alex = Usuario.objects.create_user(
    email='alex@test.com',
    nombre='Alex',
    apellido='Aguero',
    telefono='1162051543',
    rol='CLIENTE'
)

# Conversacion en WhatsApp con prefijo E.164
conv_alex = ConversacionWhatsApp.objects.create(
    telefono='5491162051543',
    usuario=alex,
    rol_detectado='ALUMNA'
)

# Plan y Suscripcion activa
plan_obj = Plan.objects.create(nombre='Plan 4 Clases', cantidad_clases=4, precio=40000)
sub_alex = Suscripcion.objects.create(
    usuario=alex,
    plan=plan_obj,
    clases_restantes=3,
    estado='ACTIVO',
    fecha_inicio=timezone.localdate(),
    fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30)
)

clase = Clase.objects.create(nombre='Pilates Reformer', duracion_minutos=60, cupo_maximo=3)

# Plantilla para los Martes (isoweekday = 2) a las 19:00 hs
plantilla_martes = PlantillaTurno.objects.create(
    clase=clase,
    dia_semana=2,
    hora_inicio=datetime.time(19, 0),
    hora_fin=datetime.time(20, 0),
    is_active=True
)

# Generar turnos desde plantilla
generar_turnos_desde_plantillas()

# Buscar el próximo martes
today = timezone.localdate()
days_until_tuesday = (2 - today.isoweekday()) % 7
if days_until_tuesday == 0:
    days_until_tuesday = 7
proximo_martes = today + datetime.timedelta(days=days_until_tuesday)

turno_martes = Turno.objects.filter(clase=clase, fecha=proximo_martes, hora_inicio=datetime.time(19, 0)).first()
assert turno_martes is not None, f"Turno del martes {proximo_martes} 19:00 debería haber sido generado"
print(f"✓ Turno generado desde plantilla: {turno_martes.fecha} {turno_martes.hora_inicio} (ID: {turno_martes.id}, estado: {turno_martes.estado})")

# Inscribir a Alex en el turno para comprobar reembolso al cancelar
reserva_alex = Reserva.objects.create(
    turno=turno_martes,
    usuario=alex,
    estado='CONFIRMADA'
)
ReservaMembresia.objects.create(reserva=reserva_alex, suscripcion=sub_alex)
sub_alex.clases_restantes -= 1
sub_alex.save()
turno_martes.cupo_actual -= 1
turno_martes.save()

assert sub_alex.clases_restantes == 2

print("\n--- TEST 1: Cancelación puntual del turno desde AdminTurnoViewSet (delete_future=false) ---")
view = AdminTurnoViewSet.as_view({'delete': 'destroy'})
request = factory.delete(f'/api/admin/turnos/{turno_martes.id}/')
force_authenticate(request, user=admin_user)
response = view(request, pk=turno_martes.id)

assert response.status_code == 204, f"Esperado 204, obtuvo {response.status_code}"

# Verificar que la fila NO fue borrada de la DB, sino marcada CANCELADO y cupo_actual=0
turno_martes.refresh_from_db()
assert turno_martes.estado == 'CANCELADO', f"Esperado CANCELADO, obtuvo {turno_martes.estado}"
assert turno_martes.cupo_actual == 0, f"Esperado cupo_actual 0, obtuvo {turno_martes.cupo_actual}"
print(f"✓ Turno puntual preservado en BD con estado='CANCELADO' y cupo_actual=0.")

# Verificar que la reserva fue cancelada a tiempo y el crédito reembolsado
reserva_alex.refresh_from_db()
assert reserva_alex.estado == 'CANCELADA_TIEMPO', f"Esperado CANCELADA_TIEMPO, obtuvo {reserva_alex.estado}"
sub_alex.refresh_from_db()
assert sub_alex.clases_restantes == 3, f"Esperado 3 créditos tras reembolso, tiene {sub_alex.clases_restantes}"
print(f"✓ Reserva de alumna cancelada a tiempo y crédito devuelto correctamente (créditos: {sub_alex.clases_restantes}).")

print("\n--- TEST 2: generar_turnos_desde_plantillas() NO debe recrear el turno cancelado ---")
generar_turnos_desde_plantillas()
turnos_martes = Turno.objects.filter(clase=clase, fecha=proximo_martes, hora_inicio=datetime.time(19, 0))
assert turnos_martes.count() == 1, f"No debe haber duplicados, hay {turnos_martes.count()}"
assert turnos_martes.first().estado == 'CANCELADO', "El turno debe seguir CANCELADO"
print("✓ generar_turnos_desde_plantillas() respetó la cancelación puntual y no lo regeneró.")

print("\n--- TEST 3: AdminAgendaView NO debe retornar la clase cancelada ---")
agenda_view = AdminAgendaView.as_view()
req_agenda = factory.get(f'/api/admin/agenda/?fecha={proximo_martes.isoformat()}')
force_authenticate(req_agenda, user=admin_user)
resp_agenda = agenda_view(req_agenda)
agenda_ids = [t['id'] for t in resp_agenda.data]
assert str(turno_martes.id) not in agenda_ids, "El turno cancelado no debe aparecer en la Agenda Admin"
print("✓ AdminAgendaView excluye correctamente el turno cancelado.")

print("\n--- TEST 4: consultar_turnos_disponibles NO debe ofrecer la clase cancelada ---")
resultado_turnos = consultar_turnos_disponibles.invoke({"fecha_str": proximo_martes.isoformat()})
assert "19:00 hs" not in resultado_turnos, "El asistente no debe listar el turno cancelado de las 19:00"
print(f"✓ Asistente IA no lista el turno cancelado. Respuesta: {resultado_turnos}")

print("\n--- TEST 5: optimizar_ocupacion_proactivo no ofrece el turno cancelado ni duplica mensajes ---")
# Crear un turno válido para mañana con 1 camilla libre
manana = today + datetime.timedelta(days=1)
turno_valido = Turno.objects.create(
    clase=clase,
    fecha=manana,
    hora_inicio=datetime.time(10, 0),
    hora_fin=datetime.time(11, 0),
    cupo_actual=1,
    estado='PROGRAMADO'
)

# Crear otro turno válido para el mismo día u otro con 2 camillas libres
turno_valido_2 = Turno.objects.create(
    clase=clase,
    fecha=manana,
    hora_inicio=datetime.time(18, 0),
    hora_fin=datetime.time(19, 0),
    cupo_actual=2,
    estado='PROGRAMADO'
)

# Ejecutar el comando proactivo
call_command('optimizar_ocupacion_proactivo')

# Verificar cuántos mensajes salientes de oferta proactiva recibió Alex
mensajes_alex = MensajeWhatsAppLog.objects.filter(
    conversacion__usuario=alex,
    agente_responsable='optimizador_ocupacion_proactivo',
    direccion='SALIENTE'
)
print(f"Total mensajes proactivos enviados a Alex en esta corrida: {mensajes_alex.count()}")
assert mensajes_alex.count() == 1, f"Debe enviar exactamente 1 invitación proactiva, envió {mensajes_alex.count()}"

# Ejecutar inmediatamente por segunda vez (simulando scheduler cada 30 min)
call_command('optimizar_ocupacion_proactivo')
mensajes_alex_2 = MensajeWhatsAppLog.objects.filter(
    conversacion__usuario=alex,
    agente_responsable='optimizador_ocupacion_proactivo',
    direccion='SALIENTE'
)
print(f"Total mensajes proactivos tras segunda corrida: {mensajes_alex_2.count()}")
assert mensajes_alex_2.count() == 1, f"Anti-spam 48h debe bloquear nuevo mensaje, pero hay {mensajes_alex_2.count()}"

print("\n==========================================")
print("¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100%)!")
print("==========================================")
