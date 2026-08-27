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

from core.models import TransaccionBancaria, Plan, Suscripcion
from core.services import asignar_plan
from django.utils import timezone
import re

def extraer_datos_comprobante_ocr(imagen_url):
    """
    Simula la extracción OCR de un comprobante de pago enviado por WhatsApp.
    En la vida real, aquí llamaríamos a Google Cloud Vision API o Tesseract OCR
    y pasaríamos la imagen para buscar la palabra 'Operación' y extraer los números.
    """
    # Devuelve datos mockeados simulando una lectura exitosa para la prueba
    return {
        "mp_payment_id": "1234567890", # ID inventado
        "monto": 8000.00
    }

def conciliar_pago_comprobante(usuario, plan_id, imagen_url=None, payment_id_manual=None):
    """
    Lógica de conciliación anti-fraude descrita en el plan de implementación.
    Cruza el comprobante enviado con las transferencias reales que ingresaron por el webhook.
    """
    logger.info(f"[WHATSAPP BOT] -> Iniciando conciliación para {usuario.email}")
    
    # 1. Extracción de datos
    if payment_id_manual:
        payment_id = payment_id_manual
    else:
        datos_ocr = extraer_datos_comprobante_ocr(imagen_url)
        payment_id = datos_ocr.get("mp_payment_id")
    
    # 2. Cruce contra datos reales
    try:
        transaccion = TransaccionBancaria.objects.get(mp_payment_id=payment_id)
        
        if transaccion.estado == 'CONCILIADA':
            mensaje = "El comprobante enviado ya ha sido utilizado para acreditar un plan anteriormente. Operación rechazada."
            logger.warning(f"[ANTI-FRAUDE] {usuario.email} intentó usar un comprobante duplicado (ID: {payment_id})")
            print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")
            return False, mensaje
            
        elif transaccion.estado == 'DISPONIBLE':
            try:
                plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                return False, "El plan seleccionado no existe."

            # Acreditamos el plan
            transaccion.estado = 'CONCILIADA'
            transaccion.save()
            
            asignar_plan(usuario.id, plan.id)
            
            mensaje = f"¡Pago verificado con éxito! Tu plan {plan.nombre} ha sido acreditado y tus clases ya están habilitadas en tu perfil."
            logger.info(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}")
            print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")
            return True, mensaje
            
    except TransaccionBancaria.DoesNotExist:
        mensaje = "No encontramos ese número de operación registrado en nuestra cuenta bancaria. Por favor verifica que el comprobante sea correcto y de una transferencia reciente."
        logger.warning(f"[ANTI-FRAUDE] {usuario.email} envió un comprobante cuyo ID ({payment_id}) no figura en ingresos de MP.")
        print(f"\n[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje}\n")
        return False, mensaje

def procesar_comando_admin_efectivo(mensaje_texto):
    """
    Simula la recepción de un comando de WhatsApp por parte del administrador.
    Ejemplo de mensaje: "Cobro 12345678 1 efectivo"
    Donde: Cobro [DNI] [ID_PLAN] efectivo
    """
    partes = mensaje_texto.split()
    if len(partes) >= 4 and partes[0].lower() == "cobro" and partes[3].lower() == "efectivo":
        dni = partes[1]
        plan_id = partes[2]
        
        from core.models import Usuario
        try:
            usuario = Usuario.objects.get(dni=dni)
            plan = Plan.objects.get(id=plan_id)
            
            # Registrar ingreso en efectivo (como TransaccionBancaria simulada para cuadrar caja)
            # o simplemente asignar el plan directamente.
            asignar_plan(usuario.id, plan.id)
            
            mensaje_admin = f"✅ Cobro en efectivo registrado correctamente. Plan {plan.nombre} asignado a {usuario.nombre} {usuario.apellido}."
            mensaje_cliente = f"¡Hola {usuario.nombre}! Hemos registrado tu pago en efectivo. Tu plan {plan.nombre} ya está activo. ¡A disfrutar tus clases!"
            
            print(f"\n[WHATSAPP BOT ADMIN] -> {mensaje_admin}")
            print(f"[WHATSAPP BOT] -> {usuario.telefono or usuario.email}: {mensaje_cliente}\n")
            
            return True, mensaje_admin
            
        except Usuario.DoesNotExist:
            return False, f"No se encontró un usuario con DNI {dni}"
        except Plan.DoesNotExist:
            return False, f"No se encontró un plan con ID {plan_id}"
            
    return False, "Formato de comando incorrecto. Usa: Cobro [DNI] [ID_PLAN] efectivo"
