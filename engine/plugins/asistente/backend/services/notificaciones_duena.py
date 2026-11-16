import datetime
import logging
import threading
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from ..tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

def notificar_duena_clase_con_una_alumna(turno, motivo='cancelacion', alumna_cancelada=None):
    """
    Notifica a Débora (la dueña) por WhatsApp cuando una clase queda con solo 1 alumna.
    
    Parámetros:
    - turno: Objeto Turno a evaluar.
    - motivo: 'cancelacion' (si ocurrió tras la baja de una alumna) o 'revision_semanal' (si se detectó al revisar la próxima semana).
    - alumna_cancelada: Objeto Usuario opcional de la alumna que canceló.
    """
    if not turno or turno.estado != 'PROGRAMADO':
        return

    now = timezone.localtime()
    tz = now.tzinfo
    clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
    if timezone.is_naive(clase_dt):
        clase_dt = timezone.make_aware(clase_dt, tz)

    # Solo evaluar clases a futuro que aún no hayan comenzado
    if clase_dt <= now:
        return

    # No alertar turnos lejanos a más de 30 días
    if turno.fecha > now.date() + datetime.timedelta(days=30):
        return

    # Verificar cantidad de reservas confirmadas activas
    reservas_confirmadas = turno.reservas.filter(estado='CONFIRMADA').select_related('usuario')
    inscriptas = reservas_confirmadas.count()

    # Requisito estricto: alertar únicamente cuando la clase queda con exactamente 1 alumna
    if inscriptas != 1:
        return

    config = get_asistente_config()
    clean_duena = config.get('telefono_duena', '5491157691786')
    conversacion_duena, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_duena)

    # Si es por revisión periódica/semanal, evitar spam verificando si ya se le avisó en las últimas 24hs para este turno
    if motivo == 'revision_semanal':
        hace_24h = now - datetime.timedelta(hours=24)
        aviso_reciente = RegistroAccionIA.objects.filter(
            tipo_accion='ALERTA_CLASE_UNA_ALUMNA',
            created_at__gte=hace_24h,
            payload__turno_id=str(turno.id)
        ).exists()
        if aviso_reciente:
            return

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_semana[turno.fecha.weekday()]
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')

    reserva_activa = reservas_confirmadas.first()
    alumna = reserva_activa.usuario
    alumna_nombre = f"{alumna.nombre} {alumna.apellido}".strip() if alumna else (reserva_activa.nombre_temporal or "Alumna puntual")

    prof_obj = obtener_profesor_de_turno(turno)
    prof_nombre = prof_obj.nombre if prof_obj else "Sin asignar"

    if motivo == 'cancelacion':
        canc_str = ""
        if alumna_cancelada:
            nom_canc = f"{alumna_cancelada.nombre} {alumna_cancelada.apellido}".strip() if hasattr(alumna_cancelada, 'nombre') else str(alumna_cancelada)
            canc_str = f" tras la cancelación de *{nom_canc}*"
        msg_duena = (
            f"¡Hola Deby! ✦ Alerta de Agenda:\n\n"
            f"Te aviso que{canc_str}, la clase de *{turno.clase.nombre}* del *{dia_nom} {fecha_str} a las {hora_str} hs* (Prof. {prof_nombre}) "
            f"quedó con *solo 1 alumna inscripta*:\n"
            f"👉 *{alumna_nombre}*\n\n"
            f"Quedan 2 camillas libres disponibles en ese horario ✨."
        )
    else:
        msg_duena = (
            f"¡Hola Deby! ✦ Alerta de Agenda Semanal:\n\n"
            f"Te aviso que la clase de *{turno.clase.nombre}* del *{dia_nom} {fecha_str} a las {hora_str} hs* (Prof. {prof_nombre}) "
            f"tiene *solo 1 alumna inscripta*:\n"
            f"👉 *{alumna_nombre}*\n\n"
            f"Hay 2 camillas libres disponibles en ese turno ✨."
        )

    def _enviar():
        try:
            client = WhatsAppClient()
            client.send_text_message(clean_duena, msg_duena)

            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion_duena,
                direccion='SALIENTE',
                agente_responsable='alerta_clase_una_alumna',
                texto=msg_duena,
                tools_ejecutadas=[f"alerta_una_alumna_turno_{turno.id}"]
            )

            RegistroAccionIA.objects.create(
                conversacion=conversacion_duena,
                tipo_accion='ALERTA_CLASE_UNA_ALUMNA',
                descripcion=f"Aviso enviado a Deby: Clase {dia_nom} {fecha_str} {hora_str}hs quedó con 1 sola alumna ({alumna_nombre}). Motivo: {motivo}.",
                payload={
                    'turno_id': str(turno.id),
                    'fecha': turno.fecha.strftime('%Y-%m-%d'),
                    'hora': turno.hora_inicio.strftime('%H:%M'),
                    'dia_nom': dia_nom,
                    'clase_nombre': turno.clase.nombre,
                    'inscriptas': 1,
                    'alumna_nombre': alumna_nombre,
                    'motivo': motivo
                }
            )
            logger.info(f"[ALERTA DUENA] Notificación enviada a Deby para turno {turno.id} ({dia_nom} {fecha_str} {hora_str} hs).")
        except Exception as e:
            logger.error(f"[ALERTA DUENA ERROR] No se pudo enviar mensaje a Deby: {e}")

    threading.Thread(target=_enviar, daemon=True).start()
