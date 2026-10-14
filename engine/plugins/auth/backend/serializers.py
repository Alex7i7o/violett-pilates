from rest_framework import serializers
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
import logging
import threading
from django.conf import settings
from plugins.comunicaciones.backend.email_service import send_transactional_email

logger = logging.getLogger(__name__)
Usuario = get_user_model()

class CustomUserDetailsSerializer(UserDetailsSerializer):
    fecha_nacimiento = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sexo = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=10)
    contacto_emergencia = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    notas_medicas = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    edad = serializers.SerializerMethodField(read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = Usuario
        fields = ('id', 'email', 'nombre', 'apellido', 'telefono', 'rol', 'fecha_nacimiento', 'sexo', 'contacto_emergencia', 'notas_medicas', 'edad')
        read_only_fields = ('email', 'rol', 'edad')

    def get_edad(self, obj):
        try:
            fn = obj.ficha_medica.fecha_nacimiento
            if fn:
                from django.utils import timezone
                today = timezone.localdate()
                return today.year - fn.year - ((today.month, today.day) < (fn.month, fn.day))
        except Exception:
            pass
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            ficha = instance.ficha_medica
            data['fecha_nacimiento'] = ficha.fecha_nacimiento.strftime("%Y-%m-%d") if ficha.fecha_nacimiento else None
            data['sexo'] = ficha.sexo or ''
            data['contacto_emergencia'] = ficha.contacto_emergencia or ''
            data['notas_medicas'] = ficha.notas_medicas or ''
        except Exception:
            data['fecha_nacimiento'] = None
            data['sexo'] = ''
            data['contacto_emergencia'] = ''
            data['notas_medicas'] = ''
        return data

    def update(self, instance, validated_data):
        fn = validated_data.pop('fecha_nacimiento', None)
        sx = validated_data.pop('sexo', None)
        ce = validated_data.pop('contacto_emergencia', None)
        nm = validated_data.pop('notas_medicas', None)

        user = super().update(instance, validated_data)

        from backend_core.hooks import registry
        ficha_data = {}
        if fn is not None:
            ficha_data['fecha_nacimiento'] = fn
        if sx is not None:
            ficha_data['sexo'] = sx
        if ce is not None:
            ficha_data['contacto_emergencia'] = ce
        if nm is not None:
            ficha_data['notas_medicas'] = nm

        if ficha_data:
            registry.execute('post_admin_usuario_save', data=ficha_data, user=user)

        return user

class CustomRegisterSerializer(RegisterSerializer):
    nombre = serializers.CharField(required=True, max_length=100)
    apellido = serializers.CharField(required=True, max_length=100)
    telefono = serializers.CharField(required=True, max_length=30)
    fecha_nacimiento = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sexo = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=10)
    contacto_emergencia = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    notas_medicas = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    username = None

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict['nombre'] = self.validated_data.get('nombre', '')
        data_dict['apellido'] = self.validated_data.get('apellido', '')
        data_dict['telefono'] = self.validated_data.get('telefono', '')
        data_dict['fecha_nacimiento'] = self.validated_data.get('fecha_nacimiento', None)
        data_dict['sexo'] = self.validated_data.get('sexo', None)
        data_dict['contacto_emergencia'] = self.validated_data.get('contacto_emergencia', None)
        data_dict['notas_medicas'] = self.validated_data.get('notas_medicas', None)
        return data_dict

    def custom_signup(self, request, user):
        user.nombre = self.cleaned_data.get('nombre', '')
        user.apellido = self.cleaned_data.get('apellido', '')
        user.telefono = self.cleaned_data.get('telefono', '')
        user.rol = 'CLIENTE'
        user.save()

        # Execute hook after_usuario_created
        signup_data = {
            'fecha_nacimiento': self.cleaned_data.get('fecha_nacimiento') or (getattr(request, 'data', {}) or {}).get('fecha_nacimiento'),
            'sexo': self.cleaned_data.get('sexo') or (getattr(request, 'data', {}) or {}).get('sexo'),
            'contacto_emergencia': self.cleaned_data.get('contacto_emergencia') or (getattr(request, 'data', {}) or {}).get('contacto_emergencia'),
            'notas_medicas': self.cleaned_data.get('notas_medicas') or (getattr(request, 'data', {}) or {}).get('notas_medicas'),
        }
        try:
            from backend_core.hooks import registry
            registry.execute('after_usuario_created', signup_data, instance=user)
        except Exception as e:
            logger.error(f"Failed to execute after_usuario_created hook: {e}")

        # Direct fallback for FichaMedica in case hooks registry is bypassed
        try:
            from plugins.fichas_medicas.backend.models import FichaMedica
            import datetime
            
            raw_fn = signup_data.get('fecha_nacimiento')
            parsed_fn = None
            if raw_fn and str(raw_fn).strip():
                try:
                    parsed_fn = datetime.datetime.strptime(str(raw_fn).strip()[:10], "%Y-%m-%d").date()
                except Exception:
                    try:
                        parsed_fn = datetime.datetime.strptime(str(raw_fn).strip()[:10], "%d/%m/%Y").date()
                    except Exception:
                        parsed_fn = None

            raw_sexo = signup_data.get('sexo')
            parsed_sexo = None
            if raw_sexo and str(raw_sexo).strip():
                sx = str(raw_sexo).strip().upper()
                if sx in ['F', 'M', 'O', 'N']:
                    parsed_sexo = sx

            raw_ce = signup_data.get('contacto_emergencia')
            raw_nm = signup_data.get('notas_medicas')

            if parsed_fn or parsed_sexo or raw_ce or raw_nm:
                FichaMedica.objects.update_or_create(
                    usuario=user,
                    defaults={
                        'fecha_nacimiento': parsed_fn,
                        'sexo': parsed_sexo,
                        'contacto_emergencia': (raw_ce or '').strip(),
                        'notas_medicas': (raw_nm or '').strip(),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to save FichaMedica fallback on signup: {e}")

        def send_welcome():
            try:
                context = {
                    'user': user,
                    'login_url': getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates/app') + '/login'
                }
                send_transactional_email(
                    subject='¡Bienvenida a Violett!',
                    template_name='emails/welcome.html',
                    context=context,
                    recipient_list=[user.email]
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")
                
        threading.Thread(target=send_welcome, daemon=True).start()

    def save(self, request):
        user = super().save(request)
        return user
from dj_rest_auth.serializers import PasswordResetSerializer
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def validate_email(self, value):
        from core.models import Usuario
        self.users = list(Usuario.objects.filter(email__iexact=value, is_active=True))
        if not self.users:
            raise serializers.ValidationError("No existe un usuario activo con este correo.")
        return value

    def save(self):
        request = self.context.get('request')
        users = getattr(self, 'users', [])
        if not users:
            return

        for user in users:
            temp_key = default_token_generator.make_token(user)
            uid = user_pk_to_url_str(user)
            
            # Construir URL del frontend explícitamente para que no falle
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates/app').rstrip('/')
            reset_url = f"{frontend_url}/reset-password/{uid}/{temp_key}"
            
            context = {
                'user': user,
                'password_reset_url': reset_url,
            }
            
            def send_reset():
                try:
                    send_transactional_email(
                        subject='Violett - Restablecimiento de contraseña',
                        template_name='emails/password_reset_key_message.html',
                        context=context,
                        recipient_list=[user.email]
                    )
                except Exception as e:
                    logger.error(f"Failed to send password reset email: {e}")
            
            threading.Thread(target=send_reset, daemon=True).start()
