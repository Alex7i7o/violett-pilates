from backend_core.hooks import registry
from .models import FichaMedica


def on_enrich_admin_usuario(data, instance=None, **kwargs):
    if instance:
        try:
            ficha = instance.ficha_medica
            data['contacto_emergencia'] = ficha.contacto_emergencia
            data['notas_medicas'] = ficha.notas_medicas
            data['fecha_nacimiento'] = ficha.fecha_nacimiento.strftime("%Y-%m-%d") if ficha.fecha_nacimiento else None
            data['sexo'] = ficha.sexo
            
            # Calcular edad
            if ficha.fecha_nacimiento:
                import datetime
                from django.utils import timezone
                today = timezone.localdate()
                edad = today.year - ficha.fecha_nacimiento.year - ((today.month, today.day) < (ficha.fecha_nacimiento.month, ficha.fecha_nacimiento.day))
                data['edad'] = edad
            else:
                data['edad'] = None

        except FichaMedica.DoesNotExist:
            data['contacto_emergencia'] = ''
            data['notas_medicas'] = ''
            data['fecha_nacimiento'] = None
            data['sexo'] = ''
            data['edad'] = None
    return data

registry.register('enrich_admin_usuario', on_enrich_admin_usuario)
