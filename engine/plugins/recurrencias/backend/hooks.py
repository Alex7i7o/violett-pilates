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
