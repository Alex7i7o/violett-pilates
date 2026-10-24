from rest_framework import serializers
from .models import Profesor, PlantillaProfesor
from core.models import PlantillaTurno

class ProfesorSerializer(serializers.ModelSerializer):
    clases_fijas = serializers.SerializerMethodField()

    class Meta:
        model = Profesor
        fields = '__all__'

    def get_clases_fijas(self, obj):
        dias_nombres = {
            1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves',
            5: 'Viernes', 6: 'Sábado', 7: 'Domingo'
        }
        pps = getattr(obj, 'plantillaprofesor_set', None)
        if pps is not None:
            lista = [
                pp for pp in pps.all()
                if getattr(pp, 'plantilla', None) and pp.plantilla.is_active
            ]
            lista.sort(key=lambda x: (x.plantilla.dia_semana, x.plantilla.hora_inicio))
            return [{
                'id': str(pp.plantilla.id),
                'dia_semana': pp.plantilla.dia_semana,
                'dia_nombre': dias_nombres.get(pp.plantilla.dia_semana, f"Día {pp.plantilla.dia_semana}"),
                'hora_inicio': pp.plantilla.hora_inicio.strftime('%H:%M') if pp.plantilla.hora_inicio else '',
                'hora_fin': pp.plantilla.hora_fin.strftime('%H:%M') if pp.plantilla.hora_fin else '',
                'clase_nombre': pp.plantilla.clase.nombre if getattr(pp.plantilla, 'clase', None) else 'Clase',
            } for pp in lista]

        plantillas = PlantillaTurno.objects.filter(
            is_active=True,
            profesor_asignado__profesor=obj
        ).select_related('clase').order_by('dia_semana', 'hora_inicio')

        return [{
            'id': str(p.id),
            'dia_semana': p.dia_semana,
            'dia_nombre': dias_nombres.get(p.dia_semana, f"Día {p.dia_semana}"),
            'hora_inicio': p.hora_inicio.strftime('%H:%M') if p.hora_inicio else '',
            'hora_fin': p.hora_fin.strftime('%H:%M') if p.hora_fin else '',
            'clase_nombre': p.clase.nombre if getattr(p, 'clase', None) else 'Clase',
        } for p in plantillas]
