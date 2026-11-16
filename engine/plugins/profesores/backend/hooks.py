from backend_core.hooks import registry

def enrich_turno(data, instance=None, **kwargs):
    prof = None
    if hasattr(instance, 'profesor_asignado'):
        prof = instance.profesor_asignado.profesor
    elif instance and instance.plantilla_id and hasattr(instance.plantilla, 'profesor_asignado'):
        prof = instance.plantilla.profesor_asignado.profesor

    if prof:
        data['profesor_nombre'] = prof.nombre
        data['profesor_apellido'] = prof.apellido
        data['profesor_color'] = prof.color_identificador
        data['profesor_id'] = str(prof.id)
        data['profesor'] = str(prof.id)
    else:
        data['profesor_nombre'] = None
        data['profesor_apellido'] = None
        data['profesor_color'] = None
        data['profesor_id'] = None
        data['profesor'] = None

    return data



def enrich_plantilla(data, instance=None, **kwargs):

    if hasattr(instance, 'profesor_asignado'):

        data['profesor_nombre'] = instance.profesor_asignado.profesor.nombre

        data['profesor_apellido'] = instance.profesor_asignado.profesor.apellido

        data['profesor_id'] = str(instance.profesor_asignado.profesor.id)

        data['profesor'] = str(instance.profesor_asignado.profesor.id)

    else:

        data['profesor_nombre'] = None

        data['profesor_apellido'] = None

        data['profesor_id'] = None

        data['profesor'] = None

    return data



def on_after_plantilla_created(data, instance=None, **kwargs):
    profesor_id = data.get('profesor')
    if profesor_id and instance:
        from .models import Profesor, PlantillaProfesor, TurnoProfesor
        from core.models import Turno
        from django.utils import timezone

        prof = Profesor.objects.filter(id=profesor_id).first()
        if prof:
            PlantillaProfesor.objects.update_or_create(plantilla_id=instance.id, defaults={'profesor': prof})

            # Sincronización inmediata con turnos futuros de la Agenda
            hoy = timezone.localdate()
            turnos_coincidentes = Turno.objects.filter(
                clase=instance.clase,
                hora_inicio=instance.hora_inicio,
                fecha__gte=hoy
            ).exclude(estado='CANCELADO')

            for tc in turnos_coincidentes:
                if tc.fecha.isoweekday() == instance.dia_semana:
                    if not tc.plantilla_id:
                        tc.plantilla = instance
                        tc.save(update_fields=['plantilla'])
                    TurnoProfesor.objects.update_or_create(
                        turno=tc,
                        defaults={'profesor': prof}
                    )
    return data


def on_after_plantilla_updated(data, instance=None, **kwargs):
    profesor_id = data.get('profesor')
    if instance:
        from .models import Profesor, PlantillaProfesor, TurnoProfesor
        from core.models import Turno
        from django.utils import timezone
        from django.db.models import Q

        pp = PlantillaProfesor.objects.filter(plantilla_id=instance.id).first()
        if profesor_id:
            prof = Profesor.objects.filter(id=profesor_id).first()
            if prof:
                if pp:
                    pp.profesor = prof
                    pp.save()
                else:
                    PlantillaProfesor.objects.create(plantilla_id=instance.id, profesor=prof)

                # SINCRONIZACIÓN PERMANENTE EN CONJUNTO (ESQUEMA -> AGENDA):
                # Cada vez que se cambia un profesor en el Esquema Semanal, se actualizan automáticamente
                # todas las clases futuras generadas a partir de hoy para este día y horario.
                hoy = timezone.localdate()
                turnos_futuros = Turno.objects.filter(
                    Q(plantilla_id=instance.id) |
                    (Q(clase=instance.clase) & Q(hora_inicio=instance.hora_inicio)),
                    fecha__gte=hoy
                ).exclude(estado='CANCELADO')

                for tf in turnos_futuros:
                    if tf.fecha.isoweekday() == instance.dia_semana:
                        if not tf.plantilla_id:
                            tf.plantilla = instance
                            tf.save(update_fields=['plantilla'])
                        TurnoProfesor.objects.update_or_create(
                            turno=tf,
                            defaults={'profesor': prof}
                        )
        elif pp:
            pp.delete()
            hoy = timezone.localdate()
            turnos_futuros = Turno.objects.filter(plantilla_id=instance.id, fecha__gte=hoy).exclude(estado='CANCELADO')
            TurnoProfesor.objects.filter(turno__in=turnos_futuros).delete()

    return data



def on_after_turno_created(data, instance=None, plantilla=None, **kwargs):

    if instance and plantilla:

        from .models import PlantillaProfesor, TurnoProfesor

        pp = PlantillaProfesor.objects.filter(plantilla_id=plantilla.id).first()

        if pp:

            TurnoProfesor.objects.create(turno_id=instance.id, profesor=pp.profesor)

    return data



registry.register('after_plantilla_created', on_after_plantilla_created)

registry.register('after_plantilla_updated', on_after_plantilla_updated)

registry.register('after_turno_created', on_after_turno_created)



def on_after_turno_created_manual(data, instance=None, **kwargs):

    profesor_id = data.get('profesor')

    if profesor_id and instance:

        from .models import Profesor, TurnoProfesor

        prof = Profesor.objects.filter(id=profesor_id).first()

        if prof:

            TurnoProfesor.objects.create(turno_id=instance.id, profesor=prof)

    return data



def on_after_turno_updated_manual(data, instance=None, **kwargs):

    profesor_id = data.get('profesor')

    if instance:

        from .models import Profesor, TurnoProfesor

        tp = TurnoProfesor.objects.filter(turno_id=instance.id).first()

        if profesor_id:

            prof = Profesor.objects.filter(id=profesor_id).first()

            if prof:

                if tp:

                    tp.profesor = prof

                    tp.save()

                else:

                    TurnoProfesor.objects.create(turno_id=instance.id, profesor=prof)

        elif tp:

            tp.delete()

    return data



registry.register('after_turno_created_manual', on_after_turno_created_manual)
registry.register('after_turno_updated_manual', on_after_turno_updated_manual)

def sincronizar_profesores_esquema_con_agenda():
    """
    Garantiza que todos los turnos futuros de la Agenda reflejen con exactitud
    el profesor asignado en el Esquema Semanal (PlantillaTurno).
    """
    try:
        from .models import PlantillaProfesor, TurnoProfesor
        from core.models import Turno
        from django.utils import timezone
        hoy = timezone.localdate()

        for pp in PlantillaProfesor.objects.select_related('plantilla', 'profesor').all():
            plantilla = pp.plantilla
            prof = pp.profesor
            if not plantilla or not plantilla.is_active or not prof:
                continue

            turnos = Turno.objects.filter(
                clase=plantilla.clase,
                hora_inicio=plantilla.hora_inicio,
                fecha__gte=hoy
            ).exclude(estado='CANCELADO')

            for t in turnos:
                if t.fecha.isoweekday() == plantilla.dia_semana:
                    if not t.plantilla_id:
                        t.plantilla = plantilla
                        t.save(update_fields=['plantilla'])
                    tp = getattr(t, 'profesor_asignado', None)
                    if not tp or tp.profesor_id != prof.id:
                        TurnoProfesor.objects.update_or_create(
                            turno=t,
                            defaults={'profesor': prof}
                        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error sincronizando profesores de esquema con agenda: {e}")


