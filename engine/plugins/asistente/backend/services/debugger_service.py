import traceback
import logging
from ..models import RegistroErrorIA

logger = logging.getLogger(__name__)

def diagnosticar_error_ia(excepcion: Exception, contexto: dict = None) -> tuple:
    """
    Analiza la excepción técnica y genera un diagnóstico en lenguaje humano comprensible y ejecutivo,
    junto con la categoría del error. Retorna (tipo_error, diagnostico_humano).
    """
    msg_e = str(excepcion)
    tipo_nombre = type(excepcion).__name__

    if "select_related" in msg_e and "profesor" in msg_e:
        return "FIELD_ERROR_PROFESOR", "El modelo de Turnos en base de datos no tiene una relación directa 'profesor'. Se debe acceder a través de TurnoProfesor con obtener_profesor_de_turno."
    
    if "DoesNotExist" in tipo_nombre:
        return "OBJETO_NO_ENCONTRADO", f"Se intentó acceder a un registro que no existe en la base de datos: {msg_e}."
    
    if "RateLimit" in msg_e or "429" in msg_e or "ResourceExhausted" in tipo_nombre:
        return "RATE_LIMIT_LLM", "El proveedor de inteligencia artificial superó el límite de solicitudes por minuto. Se requiere pausar brevemente o activar el modelo alternativo."
    
    if "timeout" in msg_e.lower() or "DeadlineExceeded" in tipo_nombre:
        return "TIMEOUT_LLM", "La respuesta del proveedor de IA demoró más del tiempo máximo permitido (timeout)."

    if "APIKey" in msg_e or "invalid api key" in msg_e.lower() or "UNAUTHENTICATED" in msg_e:
        return "AUTH_API_KEY_ERROR", "La clave API del proveedor de IA es inválida, expiró o no está configurada en las variables de entorno."

    if "IntegrityError" in tipo_nombre:
        return "DATABASE_INTEGRITY", f"Conflicto de integridad en base de datos (registro duplicado o clave foránea faltante): {msg_e}."

    if "FieldError" in tipo_nombre:
        return "DJANGO_FIELD_ERROR", f"Error en la consulta de base de datos ORM por campo inválido: {msg_e}."

    return "ERROR_TECNICO_INTERNO", f"Inconveniente en la ejecución del flujo: {msg_e}."


def registrar_y_diagnosticar_error(
    conversacion,
    mensaje_usuario: str,
    excepcion: Exception,
    agente_responsable: str = "orquestador",
    contexto: dict = None
) -> tuple:
    """
    Registra el error en la bitácora de base de datos RegistroErrorIA y genera la respuesta adecuada
    según el rol (explicación ejecutiva para Deby con ticket, o mensaje cordial para clientas).
    Retorna (texto_respuesta, error_record).
    """
    clean_phone = getattr(conversacion, 'telefono', '')
    rol = getattr(conversacion, 'rol_detectado', 'PROSPECTO')
    tb = traceback.format_exc()

    tipo_error, diagnostico = diagnosticar_error_ia(excepcion, contexto)

    try:
        err_obj = RegistroErrorIA.objects.create(
            conversacion=conversacion if hasattr(conversacion, 'pk') and conversacion.pk else None,
            telefono=clean_phone,
            rol_usuario=rol,
            mensaje_usuario=mensaje_usuario,
            agente_responsable=agente_responsable,
            tipo_error=tipo_error,
            detalle_error=str(excepcion),
            diagnostico_ia=diagnostico,
            traceback_completo=tb
        )
        ticket_id = f"#ERR-{str(err_obj.id)[:8]}"
    except Exception as db_err:
        logger.error(f"[DEBUGGER] No se pudo persistir RegistroErrorIA: {db_err}")
        err_obj = None
        ticket_id = "#ERR-ALERT"

    # Notificar en consola con formato de debbuger agent
    try:
        print(f"\n🚨 [CENTINELA AGENT] Error capturado en {clean_phone} ({rol}) | Ticket: {ticket_id}", flush=True)
        print(f"• Tipo: {tipo_error}", flush=True)
        print(f"• Diagnóstico: {diagnostico}", flush=True)
        print(f"• Detalle: {str(excepcion)}\n", flush=True)
    except Exception:
        logger.error(f"[CENTINELA AGENT] Error capturado en {clean_phone} ({rol}) | Ticket: {ticket_id} | Tipo: {tipo_error} | Detalle: {str(excepcion)}")

    if rol == 'DUENA':
        # Para Débora: respuesta ejecutiva, transparente y con diagnóstico
        texto_para_usuario = (
            f"✦ Deby, ocurrió un inconveniente técnico al procesar tu solicitud:\n\n"
            f"• *Diagnóstico:* {diagnostico}\n"
            f"• *Detalle técnico:* `{str(excepcion)}`\n"
            f"• *Ticket de auditoría:* `{ticket_id}`\n\n"
            f"Ya quedó registrado en el panel de auditoría para su resolución."
        )
    else:
        # Para clientas o prospectos: respuesta cálida y empática sin tecnicismos
        nombre_alumna = ""
        if conversacion and getattr(conversacion, 'usuario', None):
            nombre_alumna = conversacion.usuario.nombre.split()[0] if conversacion.usuario.nombre else ""
        saludo = f"¡Hola {nombre_alumna}! ✦ " if nombre_alumna else "¡Hola! ✦ "
        texto_para_usuario = (
            f"{saludo}Disculpá, en este momento estoy teniendo una pequeña demora momentánea consultando el sistema. "
            f"En unos minutitos vuelvo a estar 100% disponible para ayudarte con tus clases 🌸."
        )

    return texto_para_usuario, err_obj
