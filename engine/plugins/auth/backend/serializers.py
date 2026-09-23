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
    class Meta(UserDetailsSerializer.Meta):
        model = Usuario
        fields = ('id', 'email', 'nombre', 'apellido', 'telefono', 'rol')
        read_only_fields = ('email', 'rol')

class CustomRegisterSerializer(RegisterSerializer):
    nombre = serializers.CharField(required=True, max_length=100)
    apellido = serializers.CharField(required=True, max_length=100)
    telefono = serializers.CharField(required=True, max_length=30)
    username = None

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict['nombre'] = self.validated_data.get('nombre', '')
        data_dict['apellido'] = self.validated_data.get('apellido', '')
        data_dict['telefono'] = self.validated_data.get('telefono', '')
        return data_dict

    def custom_signup(self, request, user):
        user.nombre = self.cleaned_data.get('nombre', '')
        user.apellido = self.cleaned_data.get('apellido', '')
        user.telefono = self.cleaned_data.get('telefono', '')
        user.rol = 'CLIENTE'
        user.save()

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
