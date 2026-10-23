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
            registry.execute('reserva_creada', existing_reserva)
        else:
            r = Reserva.objects.create(
                turno=ft,
                usuario=user,
                es_recurrente=True,
                estado='CONFIRMADA'
            )
            ReservaMembresia.objects.create(reserva=r, suscripcion=suscripcion)
            registry.execute('reserva_creada', r)
        
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
        
    from core.models import Usuario, Turno, Reserva
    from .models import Recurrencia
    from django.utils import timezone
    now = timezone.localdate()
    
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
        # current recurrencias for this slot (registered)
        current_recs = Recurrencia.objects.filter(
            clase=instance.clase,
            dia_semana=instance.dia_semana,
            hora_inicio=instance.hora_inicio,
            usuario__isnull=False
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

    alumnos_manuales = data.get('alumnos_manuales', None)
    if alumnos_manuales is not None:
        current_manual = list(Recurrencia.objects.filter(
            clase=instance.clase,
            dia_semana=instance.dia_semana,
            hora_inicio=instance.hora_inicio,
            usuario__isnull=True,
            is_active=True
        ))
        
        kept_rec_ids = set()
        for item in alumnos_manuales:
            nom = (item.get('nombre') or item.get('nombre_temporal') or '').strip()
            tel = (item.get('telefono') or item.get('telefono_temporal') or '').strip()
            rec_id = item.get('id')
            if not nom:
                continue
            
            rec_obj = None
            if rec_id:
                rec_obj = Recurrencia.objects.filter(id=rec_id).first()
                
            if rec_obj:
                rec_obj.nombre_temporal = nom
                rec_obj.telefono_temporal = tel
                rec_obj.is_active = True
                rec_obj.save()
            else:
                rec_obj = Recurrencia.objects.create(
                    clase=instance.clase,
                    dia_semana=instance.dia_semana,
                    hora_inicio=instance.hora_inicio,
                    usuario=None,
                    nombre_temporal=nom,
                    telefono_temporal=tel,
                    is_active=True
                )
            kept_rec_ids.add(str(rec_obj.id))
            
            # Asignar a turnos futuros existentes
            future_turnos = Turno.objects.filter(
                clase=instance.clase,
                fecha__gte=now,
                hora_inicio=instance.hora_inicio,
                estado='PROGRAMADO'
            )
            for ft in future_turnos:
                if ft.fecha.isoweekday() == instance.dia_semana:
                    has_res = Reserva.objects.filter(
                        turno=ft,
                        usuario__isnull=True,
                        nombre_temporal__iexact=nom,
                        estado='CONFIRMADA'
                    ).exists()
                    if not has_res and ft.cupo_actual > 0:
                        Reserva.objects.create(
                            turno=ft,
                            usuario=None,
                            nombre_temporal=nom,
                            telefono_temporal=tel,
                            tipo_reserva='MANUAL_TEMPORAL',
                            es_recurrente=True,
                            estado='CONFIRMADA'
                        )
                        ft.cupo_actual = max(0, ft.cupo_actual - 1)
                        ft.save()

        # Quitar manuales que ya no estén
        for old_rec in current_manual:
            if str(old_rec.id) not in kept_rec_ids:
                old_rec.is_active = False
                old_rec.save()
                
                future_turnos = Turno.objects.filter(
                    clase=instance.clase,
                    fecha__gte=now,
                    hora_inicio=instance.hora_inicio,
                    estado='PROGRAMADO'
                )
                for ft in future_turnos:
                    if ft.fecha.isoweekday() == instance.dia_semana:
                        to_cancel = Reserva.objects.filter(
                            turno=ft,
                            usuario__isnull=True,
                            nombre_temporal__iexact=old_rec.nombre_temporal,
                            estado='CONFIRMADA',
                            es_recurrente=True
                        )
                        for r in to_cancel:
                            r.estado = 'CANCELADA_TIEMPO'
                            r.save()
                            ft.cupo_actual += 1
                            ft.save()
                
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
        data['alumnos'] = [str(r.usuario_id) for r in recs if r.usuario_id]
        data['alumnos_manuales'] = [
            {
                'id': str(r.id),
                'nombre_temporal': r.nombre_temporal,
                'telefono_temporal': r.telefono_temporal or ''
            }
            for r in recs if not r.usuario_id
        ]
    return data

registry.register('plantilla_serializer', enrich_plantilla_with_alumnos)

def on_after_turno_created(data, instance=None, plantilla=None, **kwargs):
    if not instance:
        return data
    from .models import Recurrencia
    from core.models import Reserva
    
    active_recs = Recurrencia.objects.filter(
        clase=instance.clase,
        dia_semana=instance.fecha.isoweekday(),
        hora_inicio=instance.hora_inicio,
        is_active=True
    )
    
    for rec in active_recs:
        if instance.cupo_actual <= 0:
            break
            
        if not rec.usuario and rec.nombre_temporal:
            if not Reserva.objects.filter(turno=instance, usuario__isnull=True, nombre_temporal__iexact=rec.nombre_temporal, estado='CONFIRMADA').exists():
                Reserva.objects.create(
                    turno=instance,
                    usuario=None,
                    nombre_temporal=rec.nombre_temporal,
                    telefono_temporal=rec.telefono_temporal or '',
                    tipo_reserva='MANUAL_TEMPORAL',
                    es_recurrente=True,
                    estado='CONFIRMADA'
                )
                instance.cupo_actual = max(0, instance.cupo_actual - 1)
                instance.save()
                
        elif rec.usuario:
            try:
                from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
                sub = Suscripcion.objects.filter(
                    usuario=rec.usuario,
                    estado='ACTIVO',
                    clases_restantes__gt=0,
                    fecha_vencimiento__gte=instance.fecha
                ).order_by('fecha_vencimiento').first()
                if sub:
                    if not Reserva.objects.filter(turno=instance, usuario=rec.usuario, estado='CONFIRMADA').exists():
                        r = Reserva.objects.create(
                            turno=instance,
                            usuario=rec.usuario,
                            es_recurrente=True,
                            estado='CONFIRMADA'
                        )
                        ReservaMembresia.objects.create(reserva=r, suscripcion=sub)
                        sub.clases_restantes -= 1
                        if sub.clases_restantes <= 0:
                            sub.estado = 'AGOTADO'
                        sub.save()
                        instance.cupo_actual = max(0, instance.cupo_actual - 1)
                        instance.save()
                        registry.execute('reserva_creada', r)
            except Exception:
                pass
                
    return data

registry.register('after_turno_created', on_after_turno_created)


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

def on_plan_asignado_auto_agendar(data, **kwargs):
    suscripcion = data.get('suscripcion')
    usuario = data.get('usuario')
    if suscripcion and usuario:
        try:
            from .services import auto_agendar_recurrencias_usuario
            auto_agendar_recurrencias_usuario(usuario, suscripcion)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error auto-agendando recurrencias en hook plan_asignado: {e}")
    return data

registry.register('plan_asignado', on_plan_asignado_auto_agendar)

