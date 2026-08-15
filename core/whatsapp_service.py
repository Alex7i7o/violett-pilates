import logging

logger = logging.getLogger(__name__)

def notificar_cancelacion_clase(usuario, turno):
    """
    Simula enviar un mensaje de WhatsApp indicando que la clase fue cancelada.
    """
    mensaje = f"Hola {usuario.nombre}, te informamos que la clase de {turno.clase.nombre} del {turno.fecha} a las {turno.hora_inicio.strftime('%H:%M')} hs ha sido cancelada por no alcanzar el cupo mínimo. El crédito ha sido devuelto a tu plan."
    # TODO: Integración real con Meta Cloud API
    logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
    print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")

def notificar_alerta_cupo(usuarios, turno):
    """
    Simula enviar un broadcast de WhatsApp informando que hay cupo libre.
    """
    for usuario in usuarios:
        mensaje = f"¡Hola {usuario.nombre}! Se ha liberado 1 cupo para la clase de {turno.clase.nombre} mañana a las {turno.hora_inicio.strftime('%H:%M')} hs. ¡Apresúrate a reservarlo en la plataforma!"
        logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
        print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")

def notificar_recordatorio_asistencia(usuario, turno):
    """
    Simula enviar un recordatorio de WhatsApp.
    """
    mensaje = f"Hola {usuario.nombre}, te recordamos tu clase de {turno.clase.nombre} de mañana a las {turno.hora_inicio.strftime('%H:%M')} hs. ¡Te esperamos!"
    logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
    print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")

def notificar_ultima_clase(usuario):
    """
    Simula enviar un aviso de que agendó su última clase.
    """
    mensaje = f"Hola {usuario.nombre}, acabas de agendar tu última clase del plan actual. Recuerda renovarlo para no perder tus beneficios y cupos fijos."
    logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
    print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")

def notificar_vencimiento_proximo(usuario, dias):
    """
    Simula enviar un aviso preventivo de vencimiento de plan.
    """
    mensaje = f"Hola {usuario.nombre}, tu plan mensual está a punto de vencer en {dias} días. ¡No te olvides de usar tus clases restantes y renovar!"
    logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
    print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")

def notificar_liberacion_cupo(usuario):
    """
    Simula enviar un aviso de que perdió su cupo fijo por no renovar a tiempo.
    """
    mensaje = f"Hola {usuario.nombre}, tu plan ha vencido. Hemos liberado tu horario fijo semanal. Puedes volver a suscribirte en cualquier momento."
    logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
    print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")
