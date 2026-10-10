from backend_core.hooks import registry
from .models import Recurrencia
from .serializers import RecurrenciaSerializer

def on_profile_data(data, request=None, user=None, **kwargs):
    if user:
        recurrencias = Recurrencia.objects.filter(usuario=user, is_active=True).select_related('clase')
        recurrencias_data = RecurrenciaSerializer(recurrencias, many=True).data
        data['recurrencias'] = recurrencias_data
    return data

def on_book_turno_recurrente(data, request=None, user=None, turno=None, suscripcion=None, **kwargs):
    if not user or not turno:
        return data
        
    if not suscripcion:
        try:
            from plugins.membresias.backend.models import Suscripcion
            suscripcion = Suscripcion.objects.filter(
                usuario=user, 
                estado='ACTIVO',
                clases_restantes__gt=0
            ).first()
            if not suscripcion:
                return {'success': False, 'detail': 'Necesitas un plan activo con clases disponibles para agendar una reserva fija.'}
        except ImportError:
            return {'success': False, 'detail': 'Error interno: Plugin de membresías no disponible.'}
        
    if not getattr(turno, 'plantilla_id', None):
        return {'success': False, 'detail': 'Esta clase es puntual y no admite reserva recurrente.'}
        
    weekday = turno.fecha.isoweekday()
    active_recs = Recurrencia.objects.filter(
        clase=turno.clase,
        dia_semana=weekday,
        hora_inicio=turno.hora_inicio,
        is_active=True
    ).count()
    if active_recs >= turno.clase.cupo_maximo:
        return {'success': False, 'detail': 'No hay cupos fijos disponibles, solo puntuales.'}
        
    recurrencia, created = Recurrencia.objects.get_or_create(
        usuario=user,
        clase=turno.clase,
        dia_semana=weekday,
        hora_inicio=turno.hora_inicio,
        defaults={'is_active': True}
    )
    if not created and not recurrencia.is_active:
        recurrencia.is_active = True
        recurrencia.save()

    from core.models import Turno, Reserva
    from plugins.membresias.backend.models import ReservaMembresia
    future_turnos = Turno.objects.select_related('clase').prefetch_related('reservas').filter(
        clase=turno.clase,
        hora_inicio=turno.hora_inicio,
        fecha__gte=turno.fecha,
        fecha__lte=suscripcion.fecha_vencimiento,
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).order_by('fecha')

    future_turnos_list = [t for t in future_turnos if t.fecha.isoweekday() == weekday]
    

    
    reservas_creadas = 0
    for ft in future_turnos_list:
        if suscripcion.clases_restantes <= 0:
            break
            
        existing_reserva = Reserva.objects.filter(turno=ft, usuario=user).first()
        if existing_reserva:
            if existing_reserva.estado == 'CONFIRMADA':
                continue
            existing_reserva.es_recurrente = True
            existing_reserva.estado = 'CONFIRMADA'
            existing_reserva.save()
            ReservaMembresia.objects.get_or_create(reserva=existing_reserva, defaults={'suscripcion': suscripcion})
        else:
            r = Reserva.objects.create(
                turno=ft,
                usuario=user,
                es_recurrente=True,
                estado='CONFIRMADA'
            )
            ReservaMembresia.objects.create(reserva=r, suscripcion=suscripcion)
        
        ft.cupo_actual -= 1
        ft.save()
        
        suscripcion.clases_restantes -= 1
        reservas_creadas += 1

    if suscripcion.clases_restantes == 0:
        suscripcion.estado = 'AGOTADO'
    suscripcion.save()

    if reservas_creadas == 0:
        return {'success': False, 'detail': 'No se pudieron agendar turnos recurrentes (falta de cupo o plan agotado).'}
        
    return {'success': True, 'detail': 'Reserva fija confirmada exitosamente.'}

registry.register('profile_data', on_profile_data)
registry.register('book_turno_recurrente', on_book_turno_recurrente)


def handle_plantilla_alumnos(data, instance=None, old_dia=None, old_hora=None, old_clase_id=None, **kwargs):
    if not instance:
        return data
        
    from core.models import Usuario
    from .models import Recurrencia
    
    # First migrate existing recurrencias if time changed
    if old_dia and old_hora and old_clase_id:
        if old_dia != instance.dia_semana or old_hora != instance.hora_inicio or old_clase_id != instance.clase_id:
            recs = Recurrencia.objects.filter(clase_id=old_clase_id, dia_semana=old_dia, hora_inicio=old_hora)
            for rec in recs:
                rec.clase = instance.clase
                rec.dia_semana = instance.dia_semana
                rec.hora_inicio = instance.hora_inicio
                rec.save()
        
    alumnos = data.get('alumnos', None)
    if alumnos is not None:
        from core.models import Usuario
        from .models import Recurrencia
        
        # current recurrencias for this slot
        current_recs = Recurrencia.objects.filter(
            clase=instance.clase,
            dia_semana=instance.dia_semana,
            hora_inicio=instance.hora_inicio
        )
        
        new_alumnos_ids = set(str(a) for a in alumnos)
        current_alumnos_ids = set(str(r.usuario_id) for r in current_recs if r.is_active)
        
        # To add
        for alumno_id in new_alumnos_ids - current_alumnos_ids:
            usuario = Usuario.objects.filter(id=alumno_id).first()
            if usuario:
                rec, created = Recurrencia.objects.get_or_create(
                    usuario=usuario,
                    clase=instance.clase,
                    dia_semana=instance.dia_semana,
                    hora_inicio=instance.hora_inicio,
                    defaults={'is_active': True}
                )
                if not created and not rec.is_active:
                    rec.is_active = True
                    rec.save()
                    
        # To remove
        for rec in current_recs:
            if str(rec.usuario_id) not in new_alumnos_ids and rec.is_active:
                rec.is_active = False
                rec.save()
                
    return data

registry.register('after_plantilla_created', handle_plantilla_alumnos)
registry.register('after_plantilla_updated', handle_plantilla_alumnos)


def enrich_plantilla_with_alumnos(data, instance=None, **kwargs):
    if instance:
        from .models import Recurrencia
        recs = Recurrencia.objects.filter(
            clase=instance.clase,
            dia_semana=instance.dia_semana,
            hora_inicio=instance.hora_inicio,
            is_active=True
        )
        data['alumnos'] = [str(r.usuario_id) for r in recs]
    return data

registry.register('plantilla_serializer', enrich_plantilla_with_alumnos)

def on_slot_destroyed(data, clase_id=None, dia_semana=None, hora_inicio=None, **kwargs):
    if not clase_id or not dia_semana or not hora_inicio:
        return data
    from .models import Recurrencia
    Recurrencia.objects.filter(
        clase_id=clase_id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio
    ).update(is_active=False)
    return data

registry.register('after_slot_destroyed', on_slot_destroyed)
