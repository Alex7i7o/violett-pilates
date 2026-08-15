# Developed by FireSeed - Fueling Innovation
from rest_framework import serializers
from .models import Turno, Reserva, Suscripcion, Recurrencia

class TurnoSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='fecha')
    time = serializers.TimeField(source='hora_inicio', format="%H:%M")
    classType = serializers.CharField(source='clase.nombre', read_only=True)
    availableSpots = serializers.IntegerField(source='cupo_actual')
    totalSpots = serializers.IntegerField(source='clase.cupo_maximo', read_only=True)
    isBookedByMe = serializers.SerializerMethodField()
    isRecurring = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = ['id', 'date', 'time', 'classType', 'availableSpots', 'totalSpots', 'isBookedByMe', 'isRecurring']

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

class RecurrenciaSerializer(serializers.ModelSerializer):
    classType = serializers.CharField(source='clase.nombre', read_only=True)
    time = serializers.TimeField(source='hora_inicio', format="%H:%M")
    
    class Meta:
        model = Recurrencia
        fields = ['id', 'dia_semana', 'time', 'classType', 'is_active']
