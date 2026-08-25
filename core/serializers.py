# Developed by FireSeed - Fueling Innovation
from rest_framework import serializers
from .models import Turno, Reserva, Suscripcion, Recurrencia, PlantillaTurno

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

class CustomRegisterSerializer(RegisterSerializer):
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100)
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True)
    contacto_emergencia = serializers.CharField(required=False, allow_blank=True)
    notas_medicas = serializers.CharField(required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    sexo = serializers.CharField(required=False, allow_blank=True)

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict['nombre'] = self.validated_data.get('nombre', '')
        data_dict['apellido'] = self.validated_data.get('apellido', '')
        data_dict['telefono'] = self.validated_data.get('telefono', '')
        data_dict['contacto_emergencia'] = self.validated_data.get('contacto_emergencia', '')
        data_dict['notas_medicas'] = self.validated_data.get('notas_medicas', '')
        data_dict['fecha_nacimiento'] = self.validated_data.get('fecha_nacimiento', None)
        data_dict['sexo'] = self.validated_data.get('sexo', '')
        return data_dict

    def save(self, request):
        user = super().save(request)
        user.nombre = self.cleaned_data.get('nombre')
        user.apellido = self.cleaned_data.get('apellido')
        user.telefono = self.cleaned_data.get('telefono')
        user.contacto_emergencia = self.cleaned_data.get('contacto_emergencia')
        user.notas_medicas = self.cleaned_data.get('notas_medicas')
        user.fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        user.sexo = self.cleaned_data.get('sexo')
        user.rol = 'CLIENTE'
        user.save()
        return user

class RecurrenciaSerializer(serializers.ModelSerializer):
    classType = serializers.CharField(source='clase.nombre', read_only=True)
    time = serializers.TimeField(source='hora_inicio', format="%H:%M")
    
    class Meta:
        model = Recurrencia
        fields = ['id', 'dia_semana', 'time', 'classType', 'is_active']

from .models import Profesor, Usuario, Clase, Plan

class ProfesorSerializer(serializers.ModelSerializer):
    edad = serializers.SerializerMethodField()
    class Meta:
        model = Profesor
        fields = '__all__'

    def get_edad(self, obj):
        import datetime
        if not obj.fecha_nacimiento:
            return None
        today = datetime.date.today()
        return today.year - obj.fecha_nacimiento.year - ((today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day))

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
    profesor_nombre = serializers.CharField(source='profesor.nombre', read_only=True)
    profesor_apellido = serializers.CharField(source='profesor.apellido', read_only=True)

    class Meta:
        model = PlantillaTurno
        fields = '__all__'

class AdminTurnoSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer(read_only=True)
    profesor_id = serializers.PrimaryKeyRelatedField(
        queryset=Profesor.objects.all(), source='profesor', write_only=True, required=False, allow_null=True
    )
    clase_nombre = serializers.CharField(source='clase.nombre', read_only=True)
    reservas_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Turno
        fields = ['id', 'fecha', 'hora_inicio', 'hora_fin', 'cupo_actual', 'estado', 'clase', 'clase_nombre', 'profesor', 'profesor_id', 'reservas_list']

    def get_reservas_list(self, obj):
        reservas = Reserva.objects.filter(turno=obj).exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA'])
        return AdminReservaSerializer(reservas, many=True).data

class AdminUsuarioSerializer(serializers.ModelSerializer):
    plan_activo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'email', 'telefono', 'contacto_emergencia', 'notas_medicas', 'is_active', 'plan_activo', 'fecha_nacimiento', 'edad', 'sexo']

    def get_edad(self, obj):
        import datetime
        if not obj.fecha_nacimiento:
            return None
        today = datetime.date.today()
        return today.year - obj.fecha_nacimiento.year - ((today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day))

    def get_plan_activo(self, obj):
        sub = Suscripcion.objects.filter(usuario=obj, estado='ACTIVO').first()
        if sub:
            return {
                'id': sub.id,
                'nombre': sub.plan.nombre,
                'clases_restantes': sub.clases_restantes,
                'fecha_vencimiento': sub.fecha_vencimiento
            }
        return None

