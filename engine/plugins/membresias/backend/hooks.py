from backend_core.hooks import registry
from .models import Suscripcion
from django.utils import timezone
import datetime

def on_profile_data(data, request=None, user=None):
    if not user:
        return data
        
    suscripcion = Suscripcion.objects.filter(usuario=user).order_by('-fecha_inicio').first()
    if suscripcion:
        expiration_date = suscripcion.fecha_vencimiento
        days_until_expiration = (expiration_date - timezone.localdate()).days
        
        data.update({
            "activePlan": suscripcion.plan.nombre,
            "remainingClasses": suscripcion.clases_restantes,
            "totalClasses": suscripcion.plan.cantidad_clases,
            "expirationDate": expiration_date.strftime("%d/%m/%Y"),
            "daysUntilExpiration": max(0, days_until_expiration)
        })
    return data

registry.register('profile_data', on_profile_data)


def on_enrich_admin_usuario(data, instance=None, **kwargs):
    if instance:
        suscripcion = Suscripcion.objects.filter(usuario=instance).order_by('-fecha_inicio').first()
        if suscripcion:
            data['plan_activo'] = {
                'id': str(suscripcion.id),
                'plan_nombre': suscripcion.plan.nombre,
                'clases_restantes': suscripcion.clases_restantes,
                'fecha_vencimiento': suscripcion.fecha_vencimiento.strftime("%Y-%m-%d"),
                'estado': suscripcion.estado
            }
        else:
            data['plan_activo'] = None
    return data

registry.register('enrich_admin_usuario', on_enrich_admin_usuario)

def on_after_usuario_created(data, instance=None, **kwargs):
    if instance and data.get('plan_activo'):
        plan_id = data.get('plan_activo')
        try:
            from .models import Plan
            plan = Plan.objects.get(id=plan_id, is_active=True)
            Suscripcion.objects.create(
                usuario=instance,
                plan=plan,
                clases_restantes=plan.cantidad_clases,
                fecha_inicio=timezone.localdate(),
                fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
                estado='ACTIVO'
            )
        except Exception as e:
            pass
    return data

registry.register('after_usuario_created', on_after_usuario_created)

def on_pre_book_validation(data, user=None, turno=None, **kwargs):
    suscripcion = Suscripcion.objects.filter(usuario=user, estado='ACTIVO', clases_restantes__gt=0).first()
    if not suscripcion:
        data['success'] = False
        data['detail'] = "No tienes un plan activo o clases restantes."
    return data

def on_post_book_action(data, user=None, turno=None, reserva=None, **kwargs):
    suscripcion = Suscripcion.objects.filter(usuario=user, estado='ACTIVO', clases_restantes__gt=0).first()
    if suscripcion and reserva:
        from .models import ReservaMembresia
        ReservaMembresia.objects.update_or_create(reserva=reserva, defaults={'suscripcion': suscripcion})
        suscripcion.clases_restantes -= 1
        if suscripcion.clases_restantes == 0:
            suscripcion.estado = 'AGOTADO'
        suscripcion.save()
    return data

registry.register('pre_book_validation', on_pre_book_validation)
registry.register('post_book_action', on_post_book_action)

def on_reserva_cancelada_a_tiempo(data, **kwargs):
    reserva = data
    if reserva:
        from .models import ReservaMembresia
        rm = ReservaMembresia.objects.filter(reserva=reserva).first()
        if rm:
            sub = rm.suscripcion
            sub.clases_restantes += 1
            if sub.estado == 'AGOTADO':
                sub.estado = 'ACTIVO'
            sub.save()
            rm.delete()
    return data

registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)

def on_pago_confirmado(data, usuario=None, plan=None, payment_id=None, **kwargs):
    if usuario and plan:
        # Desactivar otras suscripciones
        Suscripcion.objects.filter(usuario=usuario, estado='ACTIVO').update(estado='AGOTADO')
        
        # Crear la nueva suscripcion
        Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=plan.cantidad_clases,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
            estado='ACTIVO'
        )
        print(f"[MEMBRESIA] Suscripción activada para {usuario.nombre} tras pago {payment_id}")
    return data

registry.register('pago_confirmado', on_pago_confirmado)
