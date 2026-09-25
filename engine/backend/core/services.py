# Developed by FireSeed - Fueling Innovation
from django.utils import timezone
from django.db import transaction
from .models import Turno, Reserva, Usuario
from backend_core.hooks import registry

@transaction.atomic
def process_booking(turno_id, user, is_recurring=False, request=None):
    try:
        turno = Turno.objects.select_for_update().get(id=turno_id, estado='PROGRAMADO')
    except Turno.DoesNotExist:
        return False, "Turno no encontrado o no disponible."
        
    reserva = Reserva.objects.filter(turno=turno, usuario=user).first()
    if reserva and reserva.estado == 'CONFIRMADA':
        return False, "Ya tienes una reserva para este turno."
        
    if turno.cupo_actual <= 0:
        return False, "El turno está lleno."
        
    if is_recurring:
        result = registry.execute('book_turno_recurrente', {'success': False, 'detail': 'La función de reservas fijas no está activa.'}, request=request, user=user, turno=turno)
        if not result.get('success'):
            return False, result.get('detail')
        return True, result.get('detail', 'Reserva fija confirmada exitosamente.')
    else:
        val_result = registry.execute('pre_book_validation', {'success': True, 'detail': ''}, user=user, turno=turno)
        if not val_result.get('success'):
            return False, val_result.get('detail', 'Error de validación')

        if reserva:
            reserva.es_recurrente = False
            reserva.estado = 'CONFIRMADA'
            reserva.save()
        else:
            reserva = Reserva.objects.create(
                turno=turno,
                usuario=user,
                es_recurrente=False,
                estado='CONFIRMADA'
            )
        
        turno.cupo_actual -= 1
        turno.save()
        
        registry.execute('post_book_action', {}, user=user, turno=turno, reserva=reserva)
        registry.execute('reserva_creada', reserva)
    
    return True, "Reserva confirmada exitosamente."

@transaction.atomic
def cancelar_reserva(turno_id, usuario):
    import datetime
    try:
        reserva = Reserva.objects.select_for_update().get(turno_id=turno_id, usuario=usuario, estado='CONFIRMADA')
    except Reserva.DoesNotExist:
        return False, "No tienes una reserva activa para este turno."
        
    turno = reserva.turno
    
    dt = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
    now = timezone.now()
    from backend_core.plugin_loader import get_plugin_config
    try:
        core_config = get_plugin_config('core')
        horas_limite = core_config.get('horas_limite_cancelacion', 24)
    except Exception:
        horas_limite = 24
    time_diff = dt - now
    
    if time_diff > datetime.timedelta(hours=horas_limite):
        reserva.estado = 'CANCELADA'
        reserva.save()
        turno.cupo_actual += 1
        turno.save()
        registry.execute('reserva_cancelada_a_tiempo', reserva)
        return True, f"Reserva cancelada a tiempo (>{horas_limite}hs)."
    else:
        reserva.estado = 'CANCELADA_TARDIA'
        reserva.save()
        turno.cupo_actual += 1
        turno.save()
        registry.execute('reserva_cancelada_tardia', reserva)
        return True, f"Reserva cancelada de forma tardia (<{horas_limite}hs)."

def generar_turnos_desde_plantillas():
    import datetime
    from .models import Turno, PlantillaTurno, Reserva
    
    now = timezone.localdate()
    end_date = now + datetime.timedelta(days=30)
    
    plantillas = PlantillaTurno.objects.filter(is_active=True)
    nuevos_turnos = 0
    
    for plantilla in plantillas:
        current_date = now
        while current_date <= end_date:
            if current_date.isoweekday() == plantilla.dia_semana:
                turno_exists = Turno.objects.filter(
                    plantilla=plantilla,
                    fecha=current_date,
                    hora_inicio=plantilla.hora_inicio
                ).exists()
                
                if not turno_exists:
                    nuevo_turno = Turno.objects.create(
                        plantilla=plantilla,
                        clase=plantilla.clase,
                        fecha=current_date,
                        hora_inicio=plantilla.hora_inicio,
                        hora_fin=plantilla.hora_fin,
                        cupo_actual=plantilla.clase.cupo_maximo,
                        estado='PROGRAMADO'
                    )
                    registry.execute('after_turno_created', {}, instance=nuevo_turno, plantilla=plantilla)
                    nuevos_turnos += 1
                    registry.execute('turno_creado_desde_plantilla', nuevo_turno)
                    
            current_date += datetime.timedelta(days=1)
            
    if nuevos_turnos > 0:
        print(f"[{timezone.now().strftime('%H:%M:%S')}] Generador de Plantillas: {nuevos_turnos} turnos nuevos.")
def enviar_email_bienvenida(usuario, raw_password):
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    from backend_core.plugin_loader import get_client_config

    client_id = get_client_config().get('client_id', 'violett_pilates')
    client_dir = 'estetica' if 'estetica' in client_id else 'pilates'

    context = {
        'nombre': usuario.nombre,
        'email': usuario.email,
        'password': raw_password,
        'frontend_url': settings.FRONTEND_URL
    }

    try:
        html_content = render_to_string(f'emails/welcome.html', context)
        subject = '¡Bienvenido a Violett Pilates!'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [usuario.email]
        
        msg = EmailMultiAlternatives(subject, html_content, from_email, to_email)
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Error al enviar email de bienvenida: {e}')
        return False
