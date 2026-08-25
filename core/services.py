from django.utils import timezone
import datetime
from .models import Reserva, ConfiguracionGlobal

def cancelar_reserva(turno_id, usuario):
    """
    Lógica de negocio para cancelar una reserva evaluando la regla de 24 horas.
    Retorna un tuple: (éxito_bool, mensaje)
    """
    try:
        reserva = Reserva.objects.select_for_update().get(turno_id=turno_id, usuario=usuario, estado='CONFIRMADA')
    except Reserva.DoesNotExist:
        return False, "Reserva no encontrada."
        
    turno = reserva.turno
    
    config = ConfiguracionGlobal.objects.first()
    horas_limite = config.horas_limite_cancelacion if config else 24
    
    now = timezone.now()
    turno_datetime = timezone.make_aware(datetime.datetime.combine(turno.fecha, turno.hora_inicio))
    
    # Calcular diferencia en horas
    diff_hours = (turno_datetime - now).total_seconds() / 3600.0
    
    if diff_hours >= horas_limite:
        # Cancelación a tiempo -> Devuelve crédito
        reserva.estado = 'CANCELADA_TIEMPO'
        reserva.save()
        
        suscripcion = reserva.suscripcion
        suscripcion.clases_restantes += 1
        if suscripcion.estado == 'AGOTADO':
            suscripcion.estado = 'ACTIVO'
        suscripcion.save()
        
        turno.cupo_actual += 1
        turno.save()
        
        return True, f"Reserva cancelada a tiempo (>{horas_limite}hs). Crédito devuelto exitosamente."
    else:
        # Cancelación tardía -> No devuelve crédito
        reserva.estado = 'CANCELADA_TARDIA'
        reserva.save()
        
        turno.cupo_actual += 1
        turno.save()
        
        return True, f"Reserva cancelada de forma tardía (<{horas_limite}hs). No se ha devuelto el crédito al plan."


def notificar_cancelacion_clase(usuario, turno):
    print(f"[MAIL A {usuario.email}] LAMENTAMOS INFORMARLE QUE LA CLASE DE {turno.clase.nombre} DEL {turno.fecha.strftime('%d/%m')} A LAS {turno.hora_inicio.strftime('%H:%M')} FUE CANCELADA POR NO ALCANZAR EL CUPO MINIMO. SE LE HA DEVUELTO EL CREDITO.")

def notificar_recordatorio_asistencia(usuario, turno):
    print(f"[MAIL A {usuario.email}] RECORDATORIO: SU CLASE DE {turno.clase.nombre} ES MAÑANA A LAS {turno.hora_inicio.strftime('%H:%M')}. LO ESPERAMOS.")

def notificar_alerta_cupo(usuarios, turno):
    emails = [u.email for u in usuarios]
    print(f"[MAIL A {', '.join(emails)}] URGENTE: LA CLASE DE {turno.clase.nombre} MAÑANA A LAS {turno.hora_inicio.strftime('%H:%M')} ESTA A PUNTO DE CANCELARSE POR FALTA DE ALUMNOS! INSCRIBETE AHORA Y SALVA LA CLASE.")

def evaluar_clases():
    """
    Busca todas las clases (Turnos) que comiencen exactamente dentro de 25 horas.
    """
    from django.utils import timezone
    import datetime
    from .models import Turno, Reserva, Usuario
    
    now = timezone.now()
    target_time = now + datetime.timedelta(hours=25)
    
    target_date = target_time.date()
    target_hour = target_time.time()
    
    start_time = (target_time - datetime.timedelta(minutes=1)).time()
    end_time = (target_time + datetime.timedelta(minutes=1)).time()

    turnos_a_evaluar = Turno.objects.filter(
        fecha=target_date,
        hora_inicio__gte=start_time,
        hora_inicio__lte=end_time,
        estado='PROGRAMADO',
        evaluado_25hs=False
    )
    
    evaluados = 0
    for turno in turnos_a_evaluar:
        minimo = turno.clase.cupo_minimo
        maximo = turno.clase.cupo_maximo
        inscriptos = maximo - turno.cupo_actual
        
        reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
        
        if inscriptos < minimo:
            turno.estado = 'CANCELADO'
            turno.evaluado_25hs = True
            turno.save()
            
            for reserva in reservas:
                reserva.estado = 'CANCELADA_TIEMPO'
                reserva.save()
                
                suscripcion = reserva.suscripcion
                suscripcion.clases_restantes += 1
                if suscripcion.estado == 'AGOTADO':
                    suscripcion.estado = 'ACTIVO'
                suscripcion.save()
                
                notificar_cancelacion_clase(reserva.usuario, turno)
                
        elif inscriptos == minimo:
            turno.evaluado_25hs = True
            turno.save()
            
            for reserva in reservas:
                notificar_recordatorio_asistencia(reserva.usuario, turno)
            
            usuarios_elegibles = Usuario.objects.filter(is_active=True, rol='CLIENTE').exclude(
                id__in=reservas.values_list('usuario_id', flat=True)
            ).order_by('?')[:5]
            if usuarios_elegibles.exists():
                notificar_alerta_cupo(usuarios_elegibles, turno)
                
        else:
            turno.evaluado_25hs = True
            turno.save()
            
            for reserva in reservas:
                notificar_recordatorio_asistencia(reserva.usuario, turno)
        
        evaluados += 1
            
    if evaluados > 0:
        print(f"[{now.strftime('%H:%M:%S')}] Evaluador automático: se procesaron {evaluados} clases.")

def notificar_profesores_diario():
    """
    Simula el envío de las clases del día siguiente a cada profesor.
    Se ejecutará idealmente una vez al día por la noche.
    """
    from django.utils import timezone
    import datetime
    from .models import Turno
    
    now = timezone.now()
    tomorrow = now.date() + datetime.timedelta(days=1)
    
    turnos_manana = Turno.objects.filter(
        fecha=tomorrow,
        estado='PROGRAMADO',
        profesor__isnull=False
    ).order_by('hora_inicio')
    
    profesores_turnos = {}
    for t in turnos_manana:
        if t.profesor not in profesores_turnos:
            profesores_turnos[t.profesor] = []
        profesores_turnos[t.profesor].append(t)
        
    for profesor, turnos in profesores_turnos.items():
        print(f"\n[NOTIFICACIÓN PROFESOR] Hola {profesor.nombre}, mañana dictarás:")
        for t in turnos:
            print(f"  - {t.hora_inicio.strftime('%H:%M')} : {t.clase.nombre}")
        print("¡Que tengas un excelente día de clases!\n")

def generar_turnos_desde_plantillas():
    """
    Lee las Plantillas activas y asegura que existan los Turnos para los próximos 30 días.
    Si crea un Turno nuevo, también procesa las Recurrencias de los alumnos para ese día y hora.
    """
    from django.utils import timezone
    import datetime
    from .models import Turno, PlantillaTurno, Recurrencia, Reserva
    
    now = timezone.now().date()
    end_date = now + datetime.timedelta(days=30)
    
    plantillas = PlantillaTurno.objects.filter(is_active=True)
    nuevos_turnos = 0
    reservas_creadas = 0
    
    for plantilla in plantillas:
        current_date = now
        while current_date <= end_date:
            if current_date.isoweekday() == plantilla.dia_semana:
                turno_exists = Turno.objects.filter(
                    plantilla=plantilla,
                    fecha=current_date,
                    hora_inicio=plantilla.hora_inicio
                ).exists()
                
                if not turno_exists:
                    nuevo_turno = Turno.objects.create(
                        plantilla=plantilla,
                        clase=plantilla.clase,
                        profesor=plantilla.profesor,
                        fecha=current_date,
                        hora_inicio=plantilla.hora_inicio,
                        hora_fin=plantilla.hora_fin,
                        cupo_actual=plantilla.clase.cupo_maximo,
                        estado='PROGRAMADO'
                    )
                    nuevos_turnos += 1
                    
                    recurrencias = Recurrencia.objects.filter(
                        clase=plantilla.clase,
                        dia_semana=plantilla.dia_semana,
                        hora_inicio=plantilla.hora_inicio,
                        is_active=True
                    )
                    for rec in recurrencias:
                        suscripcion = rec.usuario.suscripciones.filter(estado='ACTIVO', clases_restantes__gt=0).first()
                        if suscripcion:
                            Reserva.objects.create(
                                turno=nuevo_turno,
                                usuario=rec.usuario,
                                suscripcion=suscripcion,
                                estado='CONFIRMADA',
                                es_recurrente=True
                            )
                            nuevo_turno.cupo_actual -= 1
                            nuevo_turno.save()
                            suscripcion.clases_restantes -= 1
                            if suscripcion.clases_restantes == 0:
                                suscripcion.estado = 'AGOTADO'
                            suscripcion.save()
                            reservas_creadas += 1
            
            current_date += datetime.timedelta(days=1)
            
    if nuevos_turnos > 0:
        print(f"[{timezone.now().strftime('%H:%M:%S')}] Generador de Plantillas: {nuevos_turnos} turnos nuevos, {reservas_creadas} reservas recurrentes.")
