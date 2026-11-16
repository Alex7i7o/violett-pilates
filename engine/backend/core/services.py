# Developed by FireSeed - Fueling Innovation
from django.utils import timezone
from django.db import transaction
from .models import Turno, Reserva, Usuario, LogMovimientoClase
from backend_core.hooks import registry

def registrar_log_movimiento(usuario, turno=None, tipo_movimiento='MODIFICACION_MANUAL', reserva=None, estado_anterior='', estado_nuevo='', realizado_por='Administración', motivo=''):
    try:
        from .models import LogMovimientoClase
        return LogMovimientoClase.objects.create(
            usuario=usuario,
            turno=turno or (reserva.turno if reserva else None),
            reserva=reserva,
            tipo_movimiento=tipo_movimiento,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            realizado_por=realizado_por or 'Administración',
            motivo=motivo or ''
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error al registrar log de movimiento: {e}")
        return None


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
        registrar_log_movimiento(
            usuario=user,
            turno=turno,
            tipo_movimiento='RESERVA_CREADA',
            reserva=reserva,
            estado_anterior='',
            estado_nuevo='CONFIRMADA',
            realizado_por=getattr(user, 'nombre', '') or 'Alumno',
            motivo='Reserva puntual creada'
        )
    
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
    
    estado_ant = reserva.estado
    if time_diff > datetime.timedelta(hours=horas_limite):
        reserva.estado = 'CANCELADA_TIEMPO'
        reserva.save()
        turno.cupo_actual += 1
        turno.save()
        registry.execute('reserva_cancelada_a_tiempo', reserva)
        registrar_log_movimiento(
            usuario=usuario,
            turno=turno,
            tipo_movimiento='RESERVA_CANCELADA',
            reserva=reserva,
            estado_anterior=estado_ant,
            estado_nuevo='CANCELADA_TIEMPO',
            realizado_por=getattr(usuario, 'nombre', '') or 'Alumno',
            motivo=f'Cancelación a tiempo (>{horas_limite}hs)'
        )
        return True, f"Reserva cancelada a tiempo (>{horas_limite}hs)."
    else:
        reserva.estado = 'CANCELADA_TARDIA'
        reserva.save()
        turno.cupo_actual += 1
        turno.save()
        registry.execute('reserva_cancelada_tardia', reserva)
        registrar_log_movimiento(
            usuario=usuario,
            turno=turno,
            tipo_movimiento='RESERVA_CANCELADA',
            reserva=reserva,
            estado_anterior=estado_ant,
            estado_nuevo='CANCELADA_TARDIA',
            realizado_por=getattr(usuario, 'nombre', '') or 'Alumno',
            motivo=f'Cancelación tardía (<{horas_limite}hs)'
        )
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
    registrar_log_movimiento(
        usuario=usuario,
        turno=turno_destino,
        tipo_movimiento='RESERVA_REPROGRAMADA',
        reserva=reserva_origen,
        estado_anterior=f"{turno_origen.fecha} {turno_origen.hora_inicio}",
        estado_nuevo=f"{turno_destino.fecha} {turno_destino.hora_inicio}",
        realizado_por=getattr(usuario, 'nombre', '') or 'Alumno',
        motivo=f"Reprogramado de {turno_origen.fecha} {turno_origen.hora_inicio} a {turno_destino.fecha} {turno_destino.hora_inicio}"
    )

    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[turno_destino.fecha.weekday()]
    return True, f"¡Clase reprogramada con éxito al {dia_nom} {turno_destino.fecha.strftime('%d/%m')} a las {turno_destino.hora_inicio.strftime('%H:%M')} hs!"


@transaction.atomic
def corregir_asistencia_reserva(reserva, nuevo_estado, realizado_por='Administración', motivo='', ajustar_credito=True):
    """
    Permite a Débora / Administración corregir o cambiar el estado de asistencia de una clase
    (TOMADA, CANCELADA_TIEMPO, CANCELADA_TARDIA, AUSENTE, CONFIRMADA).
    Ajusta automáticamente los créditos del abono de la alumna para mantener la consistencia
    matemática y guarda la trazabilidad completa en LogMovimientoClase con marca modificada_manualmente.
    """
    estados_validos = ['TOMADA', 'CANCELADA_TIEMPO', 'CANCELADA_TARDIA', 'AUSENTE', 'CONFIRMADA']
    nuevo_estado = nuevo_estado.upper().strip()
    if nuevo_estado not in estados_validos:
        return False, f"Estado inválido: {nuevo_estado}. Debe ser uno de {estados_validos}", None

    estado_anterior = reserva.estado
    if estado_anterior == nuevo_estado:
        return True, "La clase ya tenía ese estado asignado.", reserva

    reserva.estado = nuevo_estado
    reserva.modificada_manualmente = True
    reserva.motivo_modificacion = motivo or f"Corregido de {estado_anterior} a {nuevo_estado}"
    reserva.modificada_por = realizado_por or 'Administración'
    reserva.fecha_modificacion = timezone.now()
    reserva.save(update_fields=['estado', 'modificada_manualmente', 'motivo_modificacion', 'modificada_por', 'fecha_modificacion'])

    usuario = reserva.usuario
    turno = reserva.turno

    # Reconciliación de créditos
    if ajustar_credito and usuario:
        try:
            from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
            sub = Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()
            
            # Caso 1: Estaba cancelada (el crédito se había liberado) y ahora se pasa a TOMADA o AUSENTE (consume clase)
            if estado_anterior.startswith('CANCELADA') and nuevo_estado in ['TOMADA', 'AUSENTE', 'CONFIRMADA']:
                if sub:
                    ReservaMembresia.objects.update_or_create(reserva=reserva, defaults={'suscripcion': sub})
                    if sub.clases_restantes > 0:
                        sub.clases_restantes -= 1
                    if sub.clases_restantes <= 0:
                        sub.estado = 'AGOTADO'
                    sub.save(update_fields=['clases_restantes', 'estado'])

            # Caso 2: Estaba TOMADA / AUSENTE / CONFIRMADA y ahora se pasa a CANCELADA_TIEMPO (se devuelve crédito)
            elif estado_anterior in ['TOMADA', 'AUSENTE', 'CONFIRMADA'] and nuevo_estado == 'CANCELADA_TIEMPO':
                rm = ReservaMembresia.objects.filter(reserva=reserva).first()
                if rm:
                    rm.delete()
                if sub:
                    sub.clases_restantes += 1
                    if sub.estado == 'AGOTADO':
                        sub.estado = 'ACTIVO'
                    sub.save(update_fields=['clases_restantes', 'estado'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error al ajustar créditos en corrección de asistencia: {e}")

    # Registrar en LogMovimientoClase
    registrar_log_movimiento(
        usuario=usuario or reserva.usuario,
        turno=turno,
        tipo_movimiento='CORRECCION_ASISTENCIA',
        reserva=reserva,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        realizado_por=realizado_por or 'Administración',
        motivo=motivo or f"Corrección de estado de asistencia: {estado_anterior} -> {nuevo_estado}"
    )

    return True, f"Clase actualizada a {nuevo_estado} exitosamente.", reserva


@transaction.atomic
def corregir_o_registrar_asistencia_retroactiva(usuario, fecha, hora_inicio=None, nuevo_estado='TOMADA', realizado_por='Administración', motivo='', ajustar_credito=True):
    """
    Permite registrar o corregir una asistencia pasada para una alumna.
    Si ya existía una reserva (incluso cancelada), la actualiza a TOMADA y descuenta el crédito correspondiente.
    Si NO existía reserva (la alumna vino pero no estaba anotada en el sistema), busca o crea el turno y genera la reserva directamente como TOMADA.
    """
    import datetime
    from .models import Turno, Reserva, Clase

    if isinstance(fecha, str):
        fecha = datetime.date.fromisoformat(fecha)

    # 1. Buscar si ya existe una reserva de esta alumna en esa fecha
    reservas_qs = Reserva.objects.filter(usuario=usuario, turno__fecha=fecha)
    if hora_inicio:
        if isinstance(hora_inicio, str):
            if len(hora_inicio) == 5:
                hora_inicio = datetime.time.fromisoformat(hora_inicio + ':00')
            else:
                hora_inicio = datetime.time.fromisoformat(hora_inicio)
        reservas_qs = reservas_qs.filter(turno__hora_inicio=hora_inicio)

    reserva_existente = reservas_qs.order_by('turno__hora_inicio').first()
    if reserva_existente:
        return corregir_asistencia_reserva(
            reserva=reserva_existente,
            nuevo_estado=nuevo_estado,
            realizado_por=realizado_por,
            motivo=motivo or f"Corrección retroactiva para {usuario.nombre} ({fecha})",
            ajustar_credito=ajustar_credito
        )

    # 2. Si no había reserva, buscar el turno correspondiente
    turnos_qs = Turno.objects.filter(fecha=fecha)
    if hora_inicio:
        turnos_qs = turnos_qs.filter(hora_inicio=hora_inicio)
    
    turno = turnos_qs.order_by('hora_inicio').first()
    if not turno:
        # Si no existe turno en ese horario, crear turno histórico para registrar la clase
        clase_def = Clase.objects.filter(is_active=True).first()
        h_ini = hora_inicio or datetime.time(19, 0)
        h_fin = (datetime.datetime.combine(fecha, h_ini) + datetime.timedelta(minutes=50)).time()
        turno = Turno.objects.create(
            clase=clase_def,
            fecha=fecha,
            hora_inicio=h_ini,
            hora_fin=h_fin,
            cupo_actual=0,
            estado='COMPLETADO'
        )

    # 3. Crear la reserva como modificada manualmente
    reserva = Reserva.objects.create(
        turno=turno,
        usuario=usuario,
        estado=nuevo_estado,
        es_recurrente=False,
        modificada_manualmente=True,
        motivo_modificacion=motivo or f"Anotada retroactivamente por {realizado_por}",
        modificada_por=realizado_por,
        fecha_modificacion=timezone.now()
    )

    # Descontar crédito del abono activo
    if ajustar_credito:
        try:
            from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
            sub = Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()
            if sub:
                ReservaMembresia.objects.update_or_create(reserva=reserva, defaults={'suscripcion': sub})
                if sub.clases_restantes > 0:
                    sub.clases_restantes -= 1
                if sub.clases_restantes <= 0:
                    sub.estado = 'AGOTADO'
                sub.save(update_fields=['clases_restantes', 'estado'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error al vincular membresía retroactiva: {e}")

    registrar_log_movimiento(
        usuario=usuario,
        turno=turno,
        tipo_movimiento='ALUMNA_ANOTADA_RETROACTIVA',
        reserva=reserva,
        estado_anterior='SIN_RESERVA',
        estado_nuevo=nuevo_estado,
        realizado_por=realizado_por,
        motivo=motivo or f"Registro retroactivo de clase dada: {fecha} {turno.hora_inicio}"
    )

    return True, f"Clase del {fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} registrada como tomada para {usuario.nombre}.", reserva


def analizar_creditos_y_motivo_alumna(alumna, target_date=None):
    """
    Analiza la situación de créditos y abonos de una alumna registrada.
    Determina si tiene créditos disponibles y, en caso contrario, explica exactamente el motivo:
    - Plan terminado / agotado
    - Plan vencido
    - Sin créditos libres porque ya tiene todas sus clases agendadas para otros días (listando las fechas)
    - Sin plan asignado
    """
    import datetime
    from django.db.models import Q
    actualizar_reservas_pasadas_a_tomadas(usuario=alumna)

    from plugins.membresias.backend.models import Suscripcion
    today = timezone.localdate()

    if isinstance(target_date, str):
        try:
            target_date = datetime.date.fromisoformat(target_date)
        except Exception:
            pass

    sub_activa = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()

    if not sub_activa:
        sub_pasada = Suscripcion.objects.filter(usuario=alumna).order_by('-fecha_vencimiento').first()
        if sub_pasada:
            motivo = f"Su último plan ({sub_pasada.plan.nombre}) finalizó el {sub_pasada.fecha_vencimiento.strftime('%d/%m/%Y')} y actualmente no registra una renovación activa."
        else:
            motivo = f"{alumna.nombre} no registra ningún plan de abono asignado en el sistema."
        return False, 0, motivo, [], None

    if sub_activa.fecha_vencimiento and sub_activa.fecha_vencimiento < today:
        motivo = f"Su plan {sub_activa.plan.nombre} ({sub_activa.plan.cantidad_clases} clases) venció el {sub_activa.fecha_vencimiento.strftime('%d/%m/%Y')} y no tiene renovación activa."
        return False, 0, motivo, [], sub_activa

    if target_date and sub_activa.fecha_vencimiento and target_date > sub_activa.fecha_vencimiento:
        motivo = f"La fecha solicitada ({target_date.strftime('%d/%m/%Y')}) es posterior al vencimiento de su plan actual ({sub_activa.fecha_vencimiento.strftime('%d/%m/%Y')})."
        return False, 0, motivo, [], sub_activa

    clases_totales = sub_activa.plan.cantidad_clases
    now = timezone.localtime()
    now_time = now.time()

    futuras = Reserva.objects.filter(
        usuario=alumna,
        estado='CONFIRMADA',
        turno__fecha__lte=sub_activa.fecha_vencimiento
    ).filter(
        Q(turno__fecha__gt=today) |
        Q(turno__fecha=today, turno__hora_inicio__gte=now_time)
    ).select_related('turno__clase').order_by('turno__fecha', 'turno__hora_inicio')

    dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    futuras_list = []
    for rf in futuras:
        t = rf.turno
        dia_nom = dias_es[t.fecha.weekday()]
        futuras_list.append({
            'reserva_id': str(rf.id),
            'turno_id': str(t.id),
            'fecha': t.fecha.isoformat(),
            'fecha_str': f"{dia_nom} {t.fecha.strftime('%d/%m')}",
            'hora_str': t.hora_inicio.strftime('%H:%M'),
            'clase_nombre': t.clase.nombre if t.clase else 'Pilates Reformer'
        })

    clases_tomadas_qs = Reserva.objects.filter(
        usuario=alumna,
        estado='TOMADA',
        turno__fecha__lte=sub_activa.fecha_vencimiento
    )
    if sub_activa.fecha_inicio:
        clases_tomadas_qs = clases_tomadas_qs.filter(turno__fecha__gte=sub_activa.fecha_inicio - datetime.timedelta(days=7))
    clases_tomadas = clases_tomadas_qs.count()
    clases_pendientes = len(futuras_list)

    creditos_libres = max(0, clases_totales - (clases_tomadas + clases_pendientes))

    if creditos_libres > 0:
        return True, creditos_libres, f"Tiene {creditos_libres} crédito(s) libre(s)", futuras_list, sub_activa

    # Motivo específico de por qué no tiene créditos:
    if clases_pendientes > 0:
        lineas_futuras = [f"• {f['fecha_str']} a las {f['hora_str']} hs ({f['clase_nombre']})" for f in futuras_list]
        motivo = (
            f"Tiene el plan **{sub_activa.plan.nombre}** ({clases_totales} clases, vence el {sub_activa.fecha_vencimiento.strftime('%d/%m/%Y')}), "
            f"pero no tiene créditos libres porque ya tiene **todas sus clases agendadas para otros días**:\n"
            + "\n".join(lineas_futuras)
        )
    elif clases_tomadas >= clases_totales:
        motivo = (
            f"Ya completó y asistió a las **{clases_tomadas} de {clases_totales} clases** de su plan **{sub_activa.plan.nombre}** "
            f"(vence el {sub_activa.fecha_vencimiento.strftime('%d/%m/%Y')}), por lo que su abono se encuentra agotado."
        )
    else:
        motivo = (
            f"Su plan **{sub_activa.plan.nombre}** no cuenta con créditos libres disponibles (0 clases restantes)."
        )

    return False, 0, motivo, futuras_list, sub_activa
