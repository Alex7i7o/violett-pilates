from rest_framework import serializers
from .models import DisponibilidadDia, ReservaEstetica
from plugins.estetica_servicios.backend.serializers import ServicioEsteticaSerializer
from core.serializers import AdminUsuarioSerializer
from core.models import Usuario


class DisponibilidadDiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisponibilidadDia
        fields = '__all__'


class ReservaEsteticaSerializer(serializers.ModelSerializer):
    servicio_detalle = ServicioEsteticaSerializer(source='servicio', read_only=True)
    usuario_detalle = AdminUsuarioSerializer(source='usuario', read_only=True)
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        required=False,
        allow_null=True
    )
    hora_fin = serializers.TimeField(required=False, allow_null=True)
    google_event_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ReservaEstetica
        fields = '__all__'
        read_only_fields = ['google_event_id']
