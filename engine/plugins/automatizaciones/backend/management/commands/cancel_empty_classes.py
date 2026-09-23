# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Turno, Reserva
from backend_core.plugin_loader import get_plugin_config
from backend_core.hooks import registry
import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Evalua turnos a las 25hs: cancela si hay pocos inscritos, alerta si hay cupo, recuerda si esta lleno.'

    def handle(self, *args, **kwargs):
        config = get_plugin_config('automatizaciones')
        rules = config.get('cancel_empty_classes', {})
        if not rules.get('enabled', False):
            return

        min_students = rules.get('min_students', 2)
        hours_before = rules.get('hours_before_class', 25)

        now = timezone.now()
        turnos = Turno.objects.filter(estado='PROGRAMADO', evaluado_25hs=False)

        cancelados = 0
        alertas = 0
        recordatorios = 0

        for turno in turnos:
            dt = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
            time_diff = dt - now
            
            if datetime.timedelta(0) < time_diff <= datetime.timedelta(hours=hours_before):
                reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
                inscritos = reservas.count()
                
                if inscritos < min_students:
                    # Escenario A: Cancelar clase
                    turno.estado = 'CANCELADO'
                    turno.evaluado_25hs = True
                    turno.save()
                    for r in reservas:
                        r.estado = 'CANCELADA'
                        r.save()
                    cancelados += 1
                    registry.execute('turno_cancelado_por_falta_cupo', turno)
                    
                elif inscritos == min_students and turno.cupo_actual > 0:
                    # Escenario B: Alerta de cupo libre
                    turno.evaluado_25hs = True
                    turno.save()
                    alertas += 1
                    registry.execute('turno_alerta_cupo', turno)
                    
                    # Y tambien mandar recordatorio a los que ya estan
                    for r in reservas:
                        registry.execute('reserva_recordatorio', r)
                        
                else:
                    # Escenario C: Clase confirmada, mandar recordatorios
                    turno.evaluado_25hs = True
                    turno.save()
                    recordatorios += 1
                    for r in reservas:
                        registry.execute('reserva_recordatorio', r)

        if cancelados or alertas or recordatorios:
            msg = f'Evaluacion 25hs terminada. Cancelados: {cancelados}, Alertas Vacantes: {alertas}, Clases Recordadas: {recordatorios}.'
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
