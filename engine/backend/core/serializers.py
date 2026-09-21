from .models import Usuario, Clase, Turno, Reserva, PlantillaTurno
from rest_framework import serializers
from backend_core.hooks import registry

class TurnoSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='fecha')
    time = serializers.TimeField(source='hora_inicio', format="%H:%M")
    classType = serializers.CharField(source='clase.nombre', read_only=True)
    availableSpots = serializers.IntegerField(source='cupo_actual')
    totalSpots = serializers.IntegerField(source='clase.cupo_maximo', read_only=True)
    isBookedByMe = serializers.SerializerMethodField()
    isRecurring = serializers.SerializerMethodField()
    allowsRecurring = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = ['id', 'date', 'time', 'classType', 'availableSpots', 'totalSpots', 'isBookedByMe', 'isRecurring', 'allowsRecurring']

    def get_allowsRecurring(self, obj):
        return bool(obj.plantilla_id)

    def get_isBookedByMe(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        # Check if active reservation exists
        return Reserva.objects.filter(turno=obj, usuario=user, estado='CONFIRMADA').exists()

    def get_isRecurring(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        reserva = Reserva.objects.filter(turno=obj, usuario=user, estado='CONFIRMADA').first()
        return reserva.es_recurrente if reserva else False

class BookTurnoSerializer(serializers.Serializer):
    turno_id = serializers.UUIDField()
    is_recurring = serializers.BooleanField(default=False)

class CancelTurnoSerializer(serializers.Serializer):
    turno_id = serializers.UUIDField()

from dj_rest_auth.registration.serializers import RegisterSerializer
import logging
logger = logging.getLogger(__name__)

class CustomRegisterSerializer(RegisterSerializer):
    username = None
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100)
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict.pop('username', None)
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

    def save(self, request):
        try:
            return super().save(request)
        except Exception as e:
            logger.error(f"Error in CustomRegisterSerializer.save: {str(e)}")
            import traceback
            traceback.print_exc()
            raise serializers.ValidationError({"server_error": f"Error saving user: {str(e)}"})


class AdminReservaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    alumno_apellido = serializers.CharField(source='usuario.apellido', read_only=True)
    alumno_id = serializers.UUIDField(source='usuario.id', read_only=True)
    class Meta:
        model = Reserva
        fields = ['id', 'alumno_id', 'alumno_nombre', 'alumno_apellido', 'estado', 'es_recurrente']

class ClaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clase
        fields = '__all__'

class PlantillaTurnoSerializer(serializers.ModelSerializer):
    clase_nombre = serializers.CharField(source='clase.nombre', read_only=True)

    class Meta:
        model = PlantillaTurno
        fields = '__all__'
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return registry.execute('plantilla_serializer', data, instance=instance)


class AdminTurnoSerializer(serializers.ModelSerializer):
    clase_nombre = serializers.CharField(source='clase.nombre', read_only=True)
    reservas_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Turno
        fields = ['id', 'fecha', 'hora_inicio', 'hora_fin', 'cupo_actual', 'estado', 'clase', 'clase_nombre', 'reservas_list']

    def get_reservas_list(self, obj):
        reservas = Reserva.objects.filter(turno=obj).exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA'])
        return AdminReservaSerializer(reservas, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        from backend_core.hooks import registry
        return registry.execute('admin_turno_serializer', data, instance=instance)


class AdminUsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=200)
    apellido = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'apellido', 'telefono', 'is_active']
        
    def create(self, validated_data):
        nombre_completo = validated_data.get('nombre', '').strip()
        parts = nombre_completo.split(' ', 1)
        if len(parts) > 1:
            validated_data['nombre'] = parts[0]
            validated_data['apellido'] = parts[1]
        else:
            validated_data['apellido'] = ''
            
        user = super().create(validated_data)
        
        # Recuperamos datos crudos del request para inyectarlos al hook
        request = self.context.get('request')
        if request:
            from backend_core.hooks import registry
            registry.execute('after_usuario_created', request.data, instance=user)
            
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        from backend_core.hooks import registry
        # El hook enrich_admin_usuario permite que los plugins inyecten data
        enriched_data = registry.execute('enrich_admin_usuario', data, instance=instance)
        return enriched_data

