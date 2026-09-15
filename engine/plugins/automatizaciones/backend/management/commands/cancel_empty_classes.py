# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Turno, Reserva
from backend_core.plugin_loader import get_plugin_config
from backend_core.hooks import registry
import datetime

class Command(BaseCommand):
    help = 'Cancela turnos con pocos inscritos faltando X horas (leido del config).'

    def handle(self, *args, **kwargs):
        # 1. Leer config del plugin
        config = get_plugin_config('automatizaciones')
        rules = config.get('cancel_empty_classes', {})
        if not rules.get('enabled', False):
            self.stdout.write("Regla cancel_empty_classes esta deshabilitada en el config.")
            return

        min_students = rules.get('min_students', 2)
        hours_before = rules.get('hours_before_class', 24)

        now = timezone.now()
        turnos = Turno.objects.filter(estado='PROGRAMADO')

        cancelados_count = 0
        for turno in turnos:
            dt = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
            time_diff = dt - now
            
            if datetime.timedelta(0) < time_diff <= datetime.timedelta(hours=hours_before):
                reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
                if reservas.count() < min_students:
                    # Cancelar turno
                    turno.estado = 'CANCELADO'
                    turno.save()
                    cancelados_count += 1
                    
                    # Disparar evento para que 'comunicaciones' y 'membresias' actuen
                    registry.execute('turno_cancelado_por_falta_cupo', turno)

        self.stdout.write(self.style.SUCCESS(f'Exito: {cancelados_count} turnos cancelados.'))
