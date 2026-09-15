from backend_core.hooks import registry

def enrich_turno(data, instance=None, **kwargs):

    if hasattr(instance, 'profesor_asignado'):

        data['profesor_nombre'] = instance.profesor_asignado.profesor.nombre

        data['profesor_apellido'] = instance.profesor_asignado.profesor.apellido

        data['profesor_color'] = instance.profesor_asignado.profesor.color_identificador

        data['profesor_id'] = str(instance.profesor_asignado.profesor.id)

        data['profesor'] = str(instance.profesor_asignado.profesor.id)

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

        from .models import Profesor, PlantillaProfesor

        prof = Profesor.objects.filter(id=profesor_id).first()

        if prof:

            PlantillaProfesor.objects.create(plantilla_id=instance.id, profesor=prof)

    return data



def on_after_plantilla_updated(data, instance=None, **kwargs):

    profesor_id = data.get('profesor')

    if instance:

        from .models import Profesor, PlantillaProfesor

        pp = PlantillaProfesor.objects.filter(plantilla_id=instance.id).first()

        if profesor_id:

            prof = Profesor.objects.filter(id=profesor_id).first()

            if prof:

                if pp:

                    pp.profesor = prof

                    pp.save()

                else:

                    PlantillaProfesor.objects.create(plantilla_id=instance.id, profesor=prof)

        elif pp:

            pp.delete()

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

