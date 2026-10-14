import datetime
import logging
from django.utils import timezone
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from backend_core.hooks import registry
from .models import FichaMedica

logger = logging.getLogger(__name__)


def parse_fecha(fecha_val):
    if not fecha_val or str(fecha_val).strip() == '':
        return None
    if isinstance(fecha_val, datetime.date):
        return fecha_val
    if isinstance(fecha_val, datetime.datetime):
        return fecha_val.date()
    try:
        s = str(fecha_val).strip()[:10]
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.datetime.strptime(s, "%d/%m/%Y").date()
        except Exception:
            return None


def parse_sexo(sexo_val):
    if not sexo_val or str(sexo_val).strip() == '':
        return None
    s = str(sexo_val).strip().upper()
    if s in ['F', 'M', 'O', 'N']:
        return s
    return None


def on_enrich_admin_usuario(data, instance=None, **kwargs):
    if instance:
        try:
            ficha = instance.ficha_medica
            data['contacto_emergencia'] = ficha.contacto_emergencia or ''
            data['notas_medicas'] = ficha.notas_medicas or ''
            data['fecha_nacimiento'] = ficha.fecha_nacimiento.strftime("%Y-%m-%d") if ficha.fecha_nacimiento else None
            data['sexo'] = ficha.sexo or ''
            
            # Calcular edad
            if ficha.fecha_nacimiento:
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


def save_or_update_ficha(user, data):
    if not user or not data:
        return
    try:
        defaults = {}
        if 'fecha_nacimiento' in data:
            defaults['fecha_nacimiento'] = parse_fecha(data.get('fecha_nacimiento'))
        if 'sexo' in data:
            defaults['sexo'] = parse_sexo(data.get('sexo'))
        if 'contacto_emergencia' in data:
            ce = data.get('contacto_emergencia')
            defaults['contacto_emergencia'] = str(ce).strip() if ce is not None else ''
        if 'notas_medicas' in data:
            nm = data.get('notas_medicas')
            defaults['notas_medicas'] = str(nm).strip() if nm is not None else ''

        if defaults:
            FichaMedica.objects.update_or_create(
                usuario=user,
                defaults=defaults
            )
    except Exception as e:
        logger.error(f"Error saving FichaMedica for user {getattr(user, 'id', None)}: {e}")


def on_after_usuario_created(data, instance=None, **kwargs):
    if instance:
        save_or_update_ficha(instance, data)
    return data

registry.register('after_usuario_created', on_after_usuario_created)


def on_post_admin_usuario_save(data, user=None, **kwargs):
    if user:
        save_or_update_ficha(user, data)
    return data

registry.register('post_admin_usuario_save', on_post_admin_usuario_save)


@receiver(user_signed_up)
def save_ficha_medica_on_signup(request, user, **kwargs):
    req_data = getattr(request, 'data', None)
    if req_data:
        save_or_update_ficha(user, req_data)


def on_profile_data(data, request=None, user=None, **kwargs):
    if user:
        try:
            ficha = user.ficha_medica
            data['contacto_emergencia'] = ficha.contacto_emergencia or ''
            data['notas_medicas'] = ficha.notas_medicas or ''
            data['fecha_nacimiento'] = ficha.fecha_nacimiento.strftime("%Y-%m-%d") if ficha.fecha_nacimiento else None
            data['sexo'] = ficha.sexo or ''
            if ficha.fecha_nacimiento:
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

        # Detectar si el perfil está incompleto (faltan datos personales/médicos clave)
        campos_faltantes = []
        if not data.get('fecha_nacimiento'):
            campos_faltantes.append('fecha_nacimiento')
        if not data.get('sexo'):
            campos_faltantes.append('sexo')
        if not data.get('contacto_emergencia'):
            campos_faltantes.append('contacto_emergencia')
        if not getattr(user, 'telefono', None):
            campos_faltantes.append('telefono')

        data['perfil_incompleto'] = len(campos_faltantes) > 0
        data['campos_pendientes'] = campos_faltantes
    return data

registry.register('profile_data', on_profile_data)
