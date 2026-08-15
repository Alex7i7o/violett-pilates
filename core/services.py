from django.utils import timezone
import datetime
from .models import Reserva, ConfiguracionGlobal

def cancelar_reserva(turno_id, usuario):
    """
    Lógica de negocio para cancelar una reserva evaluando la regla de 24 horas.
    Retorna un tuple: (éxito_bool, mensaje)
    """
    try:
        reserva = Reserva.objects.select_for_update().get(turno_id=turno_id, usuario=usuario, estado='CONFIRMADA')
    except Reserva.DoesNotExist:
        return False, "Reserva no encontrada."
        
    turno = reserva.turno
    
    config = ConfiguracionGlobal.objects.first()
    horas_limite = config.horas_limite_cancelacion if config else 24
    
    now = timezone.now()
    turno_datetime = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
    
    # Calcular diferencia en horas
    diff_hours = (turno_datetime - now).total_seconds() / 3600.0
    
    if diff_hours >= horas_limite:
        # Cancelación a tiempo -> Devuelve crédito
        reserva.estado = 'CANCELADA_TIEMPO'
        reserva.save()
        
        suscripcion = reserva.suscripcion
        suscripcion.clases_restantes += 1
        if suscripcion.estado == 'AGOTADO':
            suscripcion.estado = 'ACTIVO'
        suscripcion.save()
        
        turno.cupo_actual += 1
        turno.save()
        
        return True, f"Reserva cancelada a tiempo (>{horas_limite}hs). Crédito devuelto exitosamente."
    else:
        # Cancelación tardía -> No devuelve crédito
        reserva.estado = 'CANCELADA_TARDIA'
        reserva.save()
        
        turno.cupo_actual += 1
        turno.save()
        
        return True, f"Reserva cancelada de forma tardía (<{horas_limite}hs). No se ha devuelto el crédito al plan."
