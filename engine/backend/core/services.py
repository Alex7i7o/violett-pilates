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
            detail_msg = val_result.get('detail', 'Error de validación')
            # Si el alumno no tiene créditos disponibles pero sí tiene clases agendadas a futuro, ofrecer reprogramación
            today = timezone.localdate()
            now_time = timezone.localtime().time()
            futuras = Reserva.objects.filter(
                usuario=user,
                estado='CONFIRMADA',
                turno__fecha__gte=today
            ).exclude(
                turno__fecha=today,
                turno__hora_inicio__lt=now_time
            ).select_related('turno__clase').order_by('turno__fecha', 'turno__hora_inicio')

            if futuras.exists():
                dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                futuras_list = []
                for rf in futuras:
                    t = rf.turno
                    dia_nom = dias_es[t.fecha.weekday()]
                    futuras_list.append({
                        'reserva_id': str(rf.id),
                        'turno_id': str(t.id),
                        'fecha': t.fecha.isoformat(),
                        'fecha_formateada': f"{dia_nom} {t.fecha.strftime('%d/%m')}",
                        'hora': t.hora_inicio.strftime('%H:%M'),
                        'clase_nombre': t.clase.nombre
                    })
                return False, {
                    'detail': 'No tenés créditos libres en tu plan actual, pero podés cambiar una de tus clases ya agendadas por este nuevo horario.',
                    'code': 'SIN_CREDITOS_CON_FUTURAS',
                    'reservas_futuras': futuras_list
                }

            return False, detail_msg

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

def actualizar_reservas_pasadas_a_tomadas(usuario=None):
    """
    Actualiza automaticamente a estado TOMADA todas las reservas con estado CONFIRMADA
    cuyo turno ya haya concluido en el tiempo.
    Regla de negocio: Si la fecha es vieja, se computa como clase ya tomada por la alumna,
    aun si el profesorado no paso lista manualmente.
    """
    from django.db.models import Q
    now = timezone.localtime()
    today = now.date()
    now_time = now.time()

    qs = Reserva.objects.filter(estado='CONFIRMADA')
    if usuario:
        qs = qs.filter(usuario=usuario)

    pasadas = qs.filter(
        Q(turno__fecha__lt=today) |
        Q(turno__fecha=today, turno__hora_fin__lte=now_time)
    )
    return pasadas.update(estado='TOMADA')

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
        reserva.estado = 'CANCELADA_TIEMPO'
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
                turnos_existentes = Turno.objects.filter(
                    clase=plantilla.clase,
                    fecha=current_date,
                    hora_inicio=plantilla.hora_inicio
                )
                
                if turnos_existentes.filter(estado='CANCELADO').exists():
                    # Turno puntual explícitamente cancelado por administración.
                    # No regenerar ni reactivar para esta fecha específica.
                    pass
                elif turnos_existentes.exists():
                    turno_existente = turnos_existentes.first()
                    if not turno_existente.plantilla:
                        turno_existente.plantilla = plantilla
                        turno_existente.save(update_fields=['plantilla'])
                else:
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

def enviar_email_bienvenida_profesor(usuario):
    from django.conf import settings
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    import logging
    logger = logging.getLogger(__name__)

    try:
        from allauth.account.utils import user_pk_to_url_str
        uid = user_pk_to_url_str(usuario)
    except Exception:
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))

    try:
        from allauth.account.forms import default_token_generator as allauth_token_gen
        temp_key = allauth_token_gen.make_token(usuario)
    except Exception as te:
        logger.warning(f"Allauth token generator fallo ({te}), usando token generator estandar de Django")
        temp_key = default_token_generator.make_token(usuario)

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates').rstrip('/')
    reset_url = f"{frontend_url}/reset-password/{uid}/{temp_key}"
    login_url = f"{frontend_url}/login"

    context = {
        'nombre': usuario.nombre,
        'email': usuario.email,
        'reset_url': reset_url,
        'login_url': login_url,
        'frontend_url': frontend_url
    }

    try:
        from plugins.comunicaciones.backend.email_service import send_transactional_email
        send_transactional_email(
            subject='¡Bienvenido al equipo de Violett! Configurá tu contraseña',
            template_name='emails/welcome_profesor.html',
            context=context,
            recipient_list=[usuario.email]
        )
        return True, "Enviado exitosamente"
    except Exception as e:
        err_str = str(e)
        logger.warning(f"Error en send_transactional_email: {err_str}. Intentando fallback directo...")
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')
        if 'domain' in err_str.lower() or 'not match' in err_str.lower() or '550' in err_str:
            from_email = 'Violett <onboarding@resend.dev>'

        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            html_content = render_to_string('emails/welcome_profesor.html', context)
            subject = '¡Bienvenido al equipo de Violett! Configurá tu contraseña'
            to_email = [usuario.email]
            
            msg = EmailMultiAlternatives(subject, html_content, from_email, to_email)
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=False)
            return True, "Enviado exitosamente"
        except Exception as err:
            logger.error(f'Error al enviar email de bienvenida profesor: {err}')
            return False, str(err)


@transaction.atomic
def reprogramar_reserva(usuario, turno_origen_id, turno_destino_id):
    """
    Mueve de forma atómica la reserva de una alumna desde un turno de origen a un nuevo turno de destino.
    Conserva los créditos de su abono intactos (cambio directo 1 a 1).
    """
    import datetime
    try:
        reserva_origen = Reserva.objects.select_for_update().get(
            turno_id=turno_origen_id,
            usuario=usuario,
            estado='CONFIRMADA'
        )
    except Reserva.DoesNotExist:
        return False, "No tienes una reserva activa en la clase de origen para reprogramar."

    try:
        turno_destino = Turno.objects.select_for_update().get(
            id=turno_destino_id,
            estado='PROGRAMADO'
        )
    except Turno.DoesNotExist:
        return False, "La clase de destino no existe o no está disponible."

    if turno_destino.cupo_actual <= 0:
        return False, "La clase de destino no tiene camillas disponibles."

    if Reserva.objects.filter(turno=turno_destino, usuario=usuario, estado='CONFIRMADA').exists():
        return False, "Ya tienes una reserva confirmada en la clase de destino."

    now = timezone.localtime()
    clase_destino_dt = datetime.datetime.combine(turno_destino.fecha, turno_destino.hora_inicio)
    if timezone.is_naive(clase_destino_dt):
        clase_destino_dt = timezone.make_aware(clase_destino_dt, now.tzinfo)

    if clase_destino_dt <= now:
        return False, "No puedes reprogramar a una clase que ya comenzó o concluyó."

    turno_origen = reserva_origen.turno

    # Reasignar turno conservando la reserva
    reserva_origen.turno = turno_destino
    reserva_origen.save(update_fields=['turno'])

    # Actualizar cupos atómicamente
    turno_origen.cupo_actual += 1
    turno_origen.save(update_fields=['cupo_actual'])

    turno_destino.cupo_actual -= 1
    turno_destino.save(update_fields=['cupo_actual'])

    # Ejecutar hook de evento
    registry.execute('reserva_reprogramada', reserva_origen, origen=turno_origen, destino=turno_destino)

    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[turno_destino.fecha.weekday()]
    return True, f"¡Clase reprogramada con éxito al {dia_nom} {turno_destino.fecha.strftime('%d/%m')} a las {turno_destino.hora_inicio.strftime('%H:%M')} hs!"
