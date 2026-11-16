import datetime
from django.utils import timezone
from django.db.models import Q
from core.models import Reserva
from .models import Suscripcion, ReservaMembresia

def calcular_metricas_suscripcion(suscripcion: Suscripcion, usuario=None):
    """
    Calcula con precisión matemática las métricas de una suscripción:
    - clases_totales: Total de clases del abono/plan.
    - clases_tomadas: Clases asistidas/ocurridas (TOMADA o AUSENTE) pertenecientes a este plan.
    - clases_pendientes: Clases futuras agendadas (CONFIRMADA) pertenecientes a este plan.
    - creditos_reales: Clases libres para reservar (totales - tomadas - pendientes).
    - clases_pendientes_efectivas: min(pendientes, max(0, totales - tomadas)).

    Reglas de negocio:
    1. Si una reserva está explícitamente asociada a otra suscripción vía ReservaMembresia,
       queda excluida de este cálculo.
    2. Si no tiene ReservaMembresia, solo se computa si su fecha de turno está estrictamente
       dentro del período del plan (fecha_inicio <= turno.fecha <= fecha_vencimiento).
       Nunca se restan días al inicio para evitar absorber clases de ciclos anteriores.
    3. Las clases canceladas (CANCELADA, CANCELADA_TIEMPO, CANCELADA_TARDIA) liberan crédito
       y no se computan ni como tomadas ni como pendientes.
    """
    if not usuario:
        usuario = suscripcion.usuario

    from core.services import actualizar_reservas_pasadas_a_tomadas
    actualizar_reservas_pasadas_a_tomadas(usuario=usuario)

    now = timezone.localtime()
    today = now.date()
    now_time = now.time()

    # Base de reservas que pertenecen a esta suscripción:
    # 1. Asociadas directamente a esta suscripción
    # 2. O sin asociación directa, pero dentro del rango estricto de fechas de vigencia
    qs_base = Reserva.objects.filter(usuario=usuario).filter(
        Q(consumo_suscripcion__suscripcion=suscripcion) |
        (
            Q(consumo_suscripcion__isnull=True) &
            Q(turno__fecha__gte=suscripcion.fecha_inicio, turno__fecha__lte=suscripcion.fecha_vencimiento)
        )
    )

    # Clases agendadas estrictamente a futuro
    clases_pendientes = qs_base.filter(
        estado='CONFIRMADA',
        turno__fecha__lte=suscripcion.fecha_vencimiento
    ).filter(
        Q(turno__fecha__gt=today) |
        Q(turno__fecha=today, turno__hora_inicio__gte=now_time)
    ).count()

    # Clases pasadas tomadas / asistidas (TOMADA o AUSENTE)
    clases_tomadas = qs_base.filter(
        estado__in=['TOMADA', 'AUSENTE'],
        turno__fecha__lte=suscripcion.fecha_vencimiento
    ).count()

    clases_totales = suscripcion.plan.cantidad_clases
    creditos_reales = max(0, clases_totales - (clases_tomadas + clases_pendientes))
    clases_pendientes_efectivas = min(clases_pendientes, max(0, clases_totales - clases_tomadas))

    if suscripcion.clases_restantes != creditos_reales:
        suscripcion.clases_restantes = creditos_reales
        if creditos_reales > 0 and suscripcion.estado == 'AGOTADO':
            suscripcion.estado = 'ACTIVO'
        elif creditos_reales == 0 and suscripcion.estado == 'ACTIVO':
            suscripcion.estado = 'AGOTADO'
        suscripcion.save(update_fields=['clases_restantes', 'estado'])

    return {
        'clases_totales': clases_totales,
        'clases_tomadas': clases_tomadas,
        'clases_pendientes': clases_pendientes_efectivas,
        'creditos_reales': creditos_reales,
        'clases_restantes': suscripcion.clases_restantes,
    }
