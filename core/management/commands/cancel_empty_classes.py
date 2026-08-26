# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from core.models import Turno, Reserva
import datetime

class Command(BaseCommand):
    help = 'Cancela turnos con menos de 2 inscritos faltando menos de 24 horas.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # Buscamos turnos PROGRAMADOS
        turnos = Turno.objects.prefetch_related('reservas').filter(
            estado='PROGRAMADO'
        )

        cancelados_count = 0
        for turno in turnos:
            # Combinar fecha y hora para obtener el datetime exacto del turno
            dt = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
            time_diff = dt - now
            
            # Si el turno es dentro de las proximas 24hs pero todavia no ha pasado
            if datetime.timedelta(0) < time_diff <= datetime.timedelta(hours=24):
                reservas = turno.reservas.filter(estado='CONFIRMADA')
                if reservas.count() < 2:
                    # Cancelamos el turno
                    turno.estado = 'CANCELADO'
                    turno.save()
                    cancelados_count += 1
                    
                    # Notificar al profesor
                    if turno.profesor and turno.profesor.usuario:
                        send_mail(
                            'Clase cancelada por falta de inscriptos',
                            f'Hola {turno.profesor.nombre},\n\nTe avisamos que la clase de {turno.clase.nombre} del {turno.fecha} a las {turno.hora_inicio.strftime("%H:%M")} ha sido cancelada por no llegar al minimo de inscriptos.\n\nSaludos,\nViolett Pilates',
                            'no-reply@violettpilates.com',
                            [turno.profesor.usuario.email],
                            fail_silently=True,
                        )
                    
                    # Notificar y devolver credito al alumno (si habia 1)
                    for reserva in reservas:
                        reserva.estado = 'CANCELADA'
                        reserva.save()
                        
                        if reserva.usuario.suscripcion_activa:
                            reserva.usuario.suscripcion_activa.clases_restantes += 1
                            reserva.usuario.suscripcion_activa.save()
                            
                        send_mail(
                            'Clase cancelada',
                            f'Hola {reserva.usuario.nombre},\n\nTe avisamos que la clase de {turno.clase.nombre} del {turno.fecha} ha sido cancelada por no llegar al minimo de inscriptos. Te hemos devuelto el credito de clase.\n\nSaludos,\nViolett Pilates',
                            'no-reply@violettpilates.com',
                            [reserva.usuario.email],
                            fail_silently=True,
                        )

        self.stdout.write(self.style.SUCCESS(f'Exito: {cancelados_count} turnos cancelados.'))
