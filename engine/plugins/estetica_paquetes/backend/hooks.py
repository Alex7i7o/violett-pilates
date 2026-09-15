from backend_core.hooks import registry

def on_pago_servicio_regla_confirmado(context, **kwargs):
    usuario = kwargs.get('usuario')
    servicio = kwargs.get('servicio')
    regla = kwargs.get('regla')
    
    if not usuario or not servicio or not regla:
        return context

    from .models import BilleteraCliente
    from django.utils import timezone
    import datetime

    # La billetera durará un tiempo por defecto, digamos 90 días
    duracion_dias = 90

    # Crear billetera
    BilleteraCliente.objects.create(
        usuario=usuario,
        servicio=servicio,
        sesiones_totales=regla.cantidad_sesiones,
        sesiones_restantes=regla.cantidad_sesiones,
        fecha_vencimiento=timezone.now().date() + datetime.timedelta(days=duracion_dias),
        estado='ACTIVO'
    )
    
    return context

# Registrar el hook
registry.register('pago_servicio_regla_confirmado', on_pago_servicio_regla_confirmado)
