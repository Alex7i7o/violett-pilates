import datetime
import re
import logging
from django.utils import timezone
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

@tool
def obtener_reporte_facturacion_semanal() -> str:
    """
    Retorna un reporte ejecutivo para la dueña con los ingresos de la semana,
    nuevas suscripciones activadas y cantidad de alumnos activos.
    """
    today = timezone.localdate()
    start_of_week = today - datetime.timedelta(days=today.weekday())

    try:
        from plugins.membresias.backend.models import Suscripcion, Plan
        subs_semana = Suscripcion.objects.filter(
            fecha_inicio__gte=start_of_week,
            fecha_inicio__lte=today
        ).select_related('plan', 'usuario')

        total_ingresos = sum(s.plan.precio for s in subs_semana if hasattr(s.plan, 'precio') and s.plan.precio)
        activas_totales = Suscripcion.objects.filter(estado__in=['ACTIVO', 'AGOTADO'], fecha_vencimiento__gte=today).count()
        nuevas_alumnas = subs_semana.count()

        return f"""✦ Resumen Ejecutivo de Facturación (Semana del {start_of_week.strftime('%d/%m')} al {today.strftime('%d/%m')}):
• Nuevas suscripciones/renovaciones: {nuevas_alumnas}
• Total estimado ingresado: ${total_ingresos:,.0f}
• Alumnas con membresía vigente: {activas_totales}

El plan más vendido en este período fue: {subs_semana.first().plan.nombre if subs_semana.exists() else 'Sin ventas registradas'}."""
    except Exception as e:
        logger.error(f"Error generando reporte de facturación: {e}")
        return f"Ocurrió un error al compilar los datos contables: {e}"


@tool
def obtener_reporte_ocupacion_hoy() -> str:
    """
    Retorna el estado de ocupación de las camillas de hoy: cantidad de clases dadas,
    reservas confirmadas, camillas libres y ausencias.
    """
    today = timezone.localdate()
    turnos_hoy = Turno.objects.filter(fecha=today, estado='PROGRAMADO').order_by('hora_inicio')

    if not turnos_hoy.exists():
        return f"No hay turnos programados para hoy ({today.strftime('%d/%m/%Y')})."

    total_camillas = turnos_hoy.count() * 3
    camillas_ocupadas = sum(3 - t.cupo_actual for t in turnos_hoy)
    porcentaje = (camillas_ocupadas / total_camillas * 100) if total_camillas > 0 else 0

    resultado = [
        f"✦ Ocupación del Estudio para Hoy ({today.strftime('%d/%m/%Y')}):",
        f"• Clases programadas: {turnos_hoy.count()} bloques",
        f"• Camillas ocupadas: {camillas_ocupadas} de {total_camillas} ({porcentaje:.1f}% de capacidad)",
        f"• Camillas libres en el día: {total_camillas - camillas_ocupadas}",
        "\nDetalle por horario:"
    ]

    for t in turnos_hoy:
        profe = f" - {t.profesor.nombre}" if t.profesor else ""
        resultado.append(f"• {t.hora_inicio.strftime('%H:%M')} hs: {3 - t.cupo_actual}/3 ocupadas{profe}")

    return "\n".join(resultado)


@tool
def contactar_prospectos_desde_lista(texto_con_contactos: str) -> str:
    """
    Permite a la dueña pasar una lista o texto con números de teléfono de interesadas
    para que el asistente les envíe un primer mensaje cálido de bienvenida e invitación a Violett Pilates.
    """
    # Extraer teléfonos con regex
    telefonos = re.findall(r'[\+]?[(]?[0-9]{2,4}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{4,6}', texto_con_contactos)
    if not telefonos:
        return "No pude identificar ningún número de teléfono en el texto que me pasaste. Por favor asegurate de incluir los números con código de área (ej: 11 6414-2172)."

    client = WhatsAppClient()
    contactados = 0

    for tel in telefonos:
        clean = tel.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if len(clean) == 10 and clean.startswith('11'):
            clean = f"549{clean}"

        msg = (
            "¡Hola! ✦ Te escribo desde Violett Pilates. La dueña del estudio nos comentó que estabas con ganas de "
            "conocer nuestro espacio boutique de Pilates Reformer en Ramos Mejía.\n\n"
            "Cada una de nuestras sesiones dura 60 minutos (55 min de práctica fluida en grupos de máximo 3 camillas + "
            "5 min de ritual de descompresión asistido).\n\n"
            "¿Te gustaría que te cuente sobre los horarios disponibles o cómo empezar?"
        )
        try:
            client.send_text_message(clean, msg)
            from ..models import ConversacionWhatsApp, MensajeWhatsAppLog
            conv, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean, defaults={'rol_detectado': 'PROSPECTO'})
            MensajeWhatsAppLog.objects.create(
                conversacion=conv,
                direccion='SALIENTE',
                agente_responsable='asistente_onboarding',
                texto=msg
            )
            contactados += 1
        except Exception as e:
            logger.error(f"Error enviando mensaje a prospecto {clean}: {e}")

    return f"✦ ¡Excelente! Ya le envié el mensaje de bienvenida y presentación a {contactados} contacto(s). Apenas respondan, el asistente las guiará para coordinar su primera clase."
