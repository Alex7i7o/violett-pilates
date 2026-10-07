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

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def save_ficha_medica_on_signup(request, user, **kwargs):
    fecha_nacimiento = request.data.get('fecha_nacimiento')
    sexo = request.data.get('sexo')
    contacto_emergencia = request.data.get('contacto_emergencia')
    notas_medicas = request.data.get('notas_medicas')
    if fecha_nacimiento or sexo or contacto_emergencia or notas_medicas:
        FichaMedica.objects.update_or_create(
            usuario=user,
            defaults={
                'fecha_nacimiento': fecha_nacimiento or None,
                'sexo': sexo,
                'contacto_emergencia': contacto_emergencia,
                'notas_medicas': notas_medicas
            }
        )


def on_post_admin_usuario_save(data, user=None, **kwargs):
    if user:
        fecha_nacimiento = data.get('fecha_nacimiento')
        sexo = data.get('sexo')
        if fecha_nacimiento or sexo:
            FichaMedica.objects.update_or_create(
                usuario=user,
                defaults={
                    'fecha_nacimiento': fecha_nacimiento or None,
                    'sexo': sexo
                }
            )
    return data

registry.register('post_admin_usuario_save', on_post_admin_usuario_save)

