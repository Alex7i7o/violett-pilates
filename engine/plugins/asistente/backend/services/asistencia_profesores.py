import datetime
import logging
from django.utils import timezone
from core.models import Turno, Reserva
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from ..tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

def solicitar_asistencia_clases_finalizadas(dry_run: bool = False) -> int:
    """
    Verifica las clases dictadas hoy que ya terminaron (hace al menos 5 minutos) y que aún
    tienen reservas en estado 'CONFIRMADA' (sin asistencia tomada por el profesor).
    Envía un mensaje de WhatsApp amigable a la profesora o profesor asignado consultándole
    si vinieron todas o si faltó alguna alumna.

    Retorna el total de mensajes de consulta enviados.
    """
    now = timezone.localtime()
    today = now.date()
    hora_actual = now.time()

    # Buscamos turnos de hoy que hayan terminado hace al menos 5 minutos
    limite_tiempo = (now - datetime.timedelta(minutes=5)).time()

    turnos_candidatos = Turno.objects.filter(
        fecha=today,
        estado='PROGRAMADO',
        hora_fin__lte=limite_tiempo
    ).select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').order_by('hora_inicio')

    if not turnos_candidatos.exists():
        logger.info("[ASISTENCIA PROFESORES] No hay turnos finalizados pendientes de revisión hoy.")
        return 0

    client = WhatsAppClient()
    mensajes_enviados = 0

    for turno in turnos_candidatos:
        # 1. Verificar si tiene reservas en 'CONFIRMADA'
        reservas_pendientes = [r for r in turno.reservas.all() if r.estado == 'CONFIRMADA']
        if not reservas_pendientes:
            # Si no hay reservas pendientes pero hay reservas tomadas/ausentes, marcar como COMPLETADO
            if turno.reservas.exists() and all(r.estado in ['TOMADA', 'AUSENTE', 'CANCELADA_TIEMPO', 'CANCELADA_TARDIA'] for r in turno.reservas.all()):
                turno.estado = 'COMPLETADO'
                turno.save(update_fields=['estado'])
            continue

        # 2. Identificar al profesor asignado
        profe = obtener_profesor_de_turno(turno)
        if not profe:
            logger.warning(f"[ASISTENCIA PROFESORES] Turno {turno.id} ({turno.clase.nombre} {turno.hora_inicio}) no tiene profesor asignado.")
            continue

        # 3. Obtener teléfono del profesor
        phone = getattr(profe, 'telefono', None)
        if not phone and getattr(profe, 'usuario', None):
            phone = profe.usuario.telefono

        clean_phone = str(phone or '').replace('+', '').replace(' ', '').replace('-', '')
        if not clean_phone or len(clean_phone) < 8:
            logger.warning(f"[ASISTENCIA PROFESORES] Profe {profe.nombre} {profe.apellido} no tiene teléfono válido configurado.")
            continue

        # 4. Verificar si ya le enviamos la consulta para este turno hoy (anti-spam)
        ya_notificado = RegistroAccionIA.objects.filter(
            tipo_accion='CONSULTA_ASISTENCIA_PROFESOR',
            payload__turno_id=str(turno.id)
        ).exists()

        if ya_notificado:
            continue

        # 5. Armar la lista de alumnas
        lineas_alumnas = []
        alumnas_info = []
        for r in reservas_pendientes:
            nom = f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else (r.nombre_temporal or "Alumna")
            lineas_alumnas.append(f"• {nom}")
            alumnas_info.append({
                'reserva_id': str(r.id),
                'nombre': nom
            })

        lista_txt = "\n".join(lineas_alumnas)
        hora_fmt = turno.hora_inicio.strftime('%H:%M')
        nombre_profe = profe.nombre or "profe"

        msg = (
            f"¡Hola {nombre_profe}! ✦ Finalizó tu clase de *{turno.clase.nombre}* de las *{hora_fmt} hs*.\n\n"
            f"Notamos que aún no se registró la asistencia en el sistema. Alumnas anotadas:\n"
            f"{lista_txt}\n\n"
            f"¿Vinieron todas o faltó alguna? Podés responder directamente por acá (ej: *'Vinieron todas'*, *'Faltó {alumnas_info[0]['nombre'].split()[0]}'* o *'Solo vino {alumnas_info[0]['nombre'].split()[0]}'*), o marcarlo desde tu panel web. ¡Muchas gracias! 🌸"
        )

        if dry_run:
            logger.info(f"[ASISTENCIA PROFESORES DRY-RUN] Mensaje a {clean_phone} ({nombre_profe}):\n{msg}")
            mensajes_enviados += 1
            continue

        try:
            client.send_text_message(clean_phone, msg)

            conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)
            conversacion.metadata['consulta_asistencia_activa'] = {
                'turno_id': str(turno.id),
                'profesor_id': str(profe.id),
                'profesor_nombre': profe.nombre,
                'clase_nombre': turno.clase.nombre,
                'hora': hora_fmt,
                'alumnas': alumnas_info,
                'enviado_at': timezone.now().isoformat()
            }
            conversacion.save(update_fields=['metadata'])

            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion,
                direccion='SALIENTE',
                agente_responsable='agente_asistencia_profesores',
                texto=msg
            )

            RegistroAccionIA.objects.create(
                tipo_accion='CONSULTA_ASISTENCIA_PROFESOR',
                descripcion=f"Consulta de asistencia enviada a {nombre_profe} para clase {turno.clase.nombre} ({hora_fmt} hs).",
                payload={
                    'turno_id': str(turno.id),
                    'profesor_id': str(profe.id),
                    'telefono': clean_phone,
                    'clase': turno.clase.nombre,
                    'alumnas': [a['nombre'] for a in alumnas_info]
                }
            )

            mensajes_enviados += 1
            logger.info(f"[ASISTENCIA PROFESORES] Consulta enviada a {nombre_profe} ({clean_phone}) para turno {turno.id}.")
        except Exception as e:
            logger.error(f"[ASISTENCIA PROFESORES] Error enviando WhatsApp a {nombre_profe}: {e}")

    return mensajes_enviados
