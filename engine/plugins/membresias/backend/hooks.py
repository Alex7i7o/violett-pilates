from backend_core.hooks import registry
from .models import Suscripcion
from django.utils import timezone
import datetime

def on_profile_data(data, request=None, user=None):
    if not user:
        return data
        
    suscripcion = Suscripcion.objects.filter(usuario=user, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()
    if suscripcion:
        expiration_date = suscripcion.fecha_vencimiento
        days_until_expiration = (expiration_date - timezone.localdate()).days
        
        from core.models import Reserva
        from core.services import actualizar_reservas_pasadas_a_tomadas
        from django.db.models import Q
        actualizar_reservas_pasadas_a_tomadas(usuario=user)

        now = timezone.localtime()
        today = now.date()
        now_time = now.time()

        # Solo turnos estrictamente a futuro se computan como pendientes por tomar dentro de la vigencia
        clases_pendientes = Reserva.objects.filter(
            usuario=user,
            estado='CONFIRMADA',
            turno__fecha__lte=suscripcion.fecha_vencimiento
        ).filter(
            Q(turno__fecha__gt=today) |
            Q(turno__fecha=today, turno__hora_inicio__gte=now_time)
        ).count()

        clases_tomadas_qs = Reserva.objects.filter(
            usuario=user,
            estado='TOMADA',
            turno__fecha__lte=suscripcion.fecha_vencimiento
        )
        if suscripcion.fecha_inicio:
            clases_tomadas_qs = clases_tomadas_qs.filter(turno__fecha__gte=suscripcion.fecha_inicio - datetime.timedelta(days=7))
        clases_tomadas = clases_tomadas_qs.count()

        # Reconciliación matemática: total = tomadas + pendientes + restantes
        clases_totales = suscripcion.plan.cantidad_clases
        creditos_reales = max(0, clases_totales - (clases_tomadas + clases_pendientes))
        clases_pendientes_efectivas = min(clases_pendientes, max(0, clases_totales - clases_tomadas))

        if suscripcion.clases_restantes != creditos_reales:
            suscripcion.clases_restantes = creditos_reales
            if creditos_reales > 0 and suscripcion.estado == 'AGOTADO':
                suscripcion.estado = 'ACTIVO'
            elif creditos_reales == 0 and suscripcion.estado == 'ACTIVO':
                suscripcion.estado = 'AGOTADO'
            suscripcion.save(update_fields=['clases_restantes', 'estado'])

        data.update({
            "activePlan": suscripcion.plan.nombre,
            "remainingClasses": suscripcion.clases_restantes,
            "pendingClasses": clases_pendientes_efectivas,
            "takenClasses": clases_tomadas,
            "totalClasses": clases_totales,
            "expirationDate": expiration_date.strftime("%d/%m/%Y"),
            "daysUntilExpiration": max(0, days_until_expiration)
        })
    return data

registry.register('profile_data', on_profile_data)


def on_enrich_admin_usuario(data, instance=None, **kwargs):
    if instance:
        suscripcion = Suscripcion.objects.filter(usuario=instance, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()
        if suscripcion:
            from core.models import Reserva
            from core.services import actualizar_reservas_pasadas_a_tomadas
            from django.db.models import Q
            actualizar_reservas_pasadas_a_tomadas(usuario=instance)

            now = timezone.localtime()
            today = now.date()
            now_time = now.time()

            # Clases agendadas que aun no ocurrieron dentro de la vigencia del plan
            clases_pendientes = Reserva.objects.filter(
                usuario=instance,
                estado='CONFIRMADA',
                turno__fecha__lte=suscripcion.fecha_vencimiento
            ).filter(
                Q(turno__fecha__gt=today) |
                Q(turno__fecha=today, turno__hora_inicio__gte=now_time)
            ).count()

            # Clases ya ocurridas o tomadas durante este ciclo de membresía
            clases_tomadas_qs = Reserva.objects.filter(
                usuario=instance,
                estado='TOMADA',
                turno__fecha__lte=suscripcion.fecha_vencimiento
            )
            if suscripcion.fecha_inicio:
                clases_tomadas_qs = clases_tomadas_qs.filter(turno__fecha__gte=suscripcion.fecha_inicio - datetime.timedelta(days=7))
            clases_tomadas = clases_tomadas_qs.count()

            # Reconciliación automática inteligente:
            # clases_totales = tomadas + pendientes + libres
            # Las canceladas no restan cupos, se transforman en créditos disponibles!
            clases_totales = suscripcion.plan.cantidad_clases
            creditos_reales = max(0, clases_totales - (clases_tomadas + clases_pendientes))
            clases_pendientes_efectivas = min(clases_pendientes, max(0, clases_totales - clases_tomadas))

            if suscripcion.clases_restantes != creditos_reales:
                suscripcion.clases_restantes = creditos_reales
                if creditos_reales > 0 and suscripcion.estado == 'AGOTADO':
                    suscripcion.estado = 'ACTIVO'
                elif creditos_reales == 0 and suscripcion.estado == 'ACTIVO':
                    suscripcion.estado = 'AGOTADO'
                suscripcion.save(update_fields=['clases_restantes', 'estado'])

            data['plan_activo'] = {
                'id': str(suscripcion.id),
                'plan_id': str(suscripcion.plan.id),
                'plan_nombre': suscripcion.plan.nombre,
                'clases_totales': clases_totales,
                'clases_restantes': suscripcion.clases_restantes,
                'clases_pendientes': clases_pendientes_efectivas,
                'clases_tomadas': clases_tomadas,
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
            nueva_sub = Suscripcion.objects.create(
                usuario=instance,
                plan=plan,
                clases_restantes=plan.cantidad_clases,
                fecha_inicio=timezone.localdate(),
                fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
                estado='ACTIVO'
            )
            registry.execute('plan_asignado', data={'suscripcion': nueva_sub, 'usuario': instance, 'plan': plan})
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
        from .models import ReservaMembresia, Suscripcion
        rm = ReservaMembresia.objects.filter(reserva=reserva).first()
        sub = None
        if rm:
            sub = rm.suscripcion
            rm.delete()
        elif getattr(reserva, 'usuario', None):
            sub = Suscripcion.objects.filter(usuario=reserva.usuario, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()

        if sub:
            sub.clases_restantes += 1
            if sub.estado == 'AGOTADO':
                sub.estado = 'ACTIVO'
            sub.save(update_fields=['clases_restantes', 'estado'])
    return data

registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)

def on_pago_confirmado(data, usuario=None, plan=None, payment_id=None, **kwargs):
    if usuario and plan:
        # Desactivar otras suscripciones
        Suscripcion.objects.filter(usuario=usuario, estado='ACTIVO').update(estado='AGOTADO')
        
        # Crear la nueva suscripcion
        nueva_sub = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=plan.cantidad_clases,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
            estado='ACTIVO'
        )
        registry.execute('plan_asignado', data={'suscripcion': nueva_sub, 'usuario': usuario, 'plan': plan})
        print(f"[MEMBRESIA] Suscripción activada para {usuario.nombre} tras pago {payment_id}")
    return data

registry.register('pago_confirmado', on_pago_confirmado)
