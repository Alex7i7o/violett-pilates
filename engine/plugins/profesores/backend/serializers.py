from rest_framework import serializers
from .models import Profesor, TurnoProfesor

class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = '__all__'
