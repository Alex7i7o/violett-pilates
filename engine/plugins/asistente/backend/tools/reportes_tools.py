import datetime
import calendar
import re
import logging
from collections import Counter
from django.utils import timezone
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

MESES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

@tool
def obtener_reporte_facturacion(periodo: str = "mes", mes_o_fecha: str = "") -> str:
    """
    Retorna el reporte contable y ejecutivo para la dueña (Deby) con los ingresos reales/estimados,
    cantidad de nuevas suscripciones, alumnas activas totales y desglose por plan.
    Parámetros:
    - periodo: 'mes' (por defecto), 'semana', 'hoy' o un mes específico como 'octubre'.
    - mes_o_fecha: nombre del mes específico a consultar (ej: 'octubre', 'septiembre', 'noviembre') o período libre.
    """
    today = timezone.localdate()
    texto_busqueda = f"{periodo} {mes_o_fecha}".lower().strip()

    # Detectar si se pidió un mes específico por nombre
    mes_encontrado = None
    for nombre_m, num_m in MESES_MAP.items():
        if nombre_m in texto_busqueda:
            mes_encontrado = (nombre_m, num_m)
            break

    # 1. Período Semanal
    if 'semana' in texto_busqueda and not mes_encontrado and 'no de una semana' not in texto_busqueda:
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = today
        titulo_periodo = f"Semana del {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}"
    # 2. Período Diario (Hoy)
    elif 'hoy' in texto_busqueda and not mes_encontrado:
        start_date = today
        end_date = today
        titulo_periodo = f"Hoy ({today.strftime('%d/%m/%Y')})"
    # 3. Período Mensual (Mes actual o mes específico)
    else:
        if mes_encontrado:
            nombre_mes, num_mes = mes_encontrado
            year = today.year
            # Si se consulta un mes futuro en el año calendario corriente, asumimos el año anterior
            if num_mes > today.month:
                year = today.year - 1
        else:
            num_mes = today.month
            year = today.year
            nombre_mes = [k for k, v in MESES_MAP.items() if v == num_mes][0]

        _, last_day = calendar.monthrange(year, num_mes)
        start_date = datetime.date(year, num_mes, 1)
        end_date = datetime.date(year, num_mes, last_day)
        titulo_periodo = f"Mes de {nombre_mes.capitalize()} {year} (01/{num_mes:02d} al {last_day:02d}/{num_mes:02d})"

    try:
        from plugins.membresias.backend.models import Suscripcion, Plan
        subs_periodo = Suscripcion.objects.filter(
            fecha_inicio__gte=start_date,
            fecha_inicio__lte=end_date
        ).select_related('plan', 'usuario')

        total_ingresos = sum(s.plan.precio for s in subs_periodo if hasattr(s.plan, 'precio') and s.plan.precio)
        activas_totales = Suscripcion.objects.filter(estado__in=['ACTIVO', 'AGOTADO'], fecha_vencimiento__gte=today).count()
        nuevas_alumnas = subs_periodo.count()

        conteo_planes = Counter()
        for s in subs_periodo:
            if s.plan and s.plan.nombre:
                conteo_planes[s.plan.nombre] += 1

        if conteo_planes:
            desglose = "\n".join([f"• {plan}: {cant} ventas" for plan, cant in conteo_planes.most_common()])
            plan_mas_vendido = conteo_planes.most_common(1)[0][0]
        else:
            desglose = "• Sin suscripciones registradas en este período."
            plan_mas_vendido = "Sin ventas registradas"

        return f"""✦ Resumen Ejecutivo de Facturación ({titulo_periodo}):
• Total estimado ingresado: ${total_ingresos:,.0f}
• Nuevas suscripciones/renovaciones: {nuevas_alumnas}
• Alumnas con membresía vigente: {activas_totales}

Desglose de planes vendidos:
{desglose}

El plan con más movimientos en este período fue: {plan_mas_vendido}."""

    except Exception as e:
        logger.error(f"Error generando reporte de facturación: {e}", exc_info=True)
        return f"Ocurrió un error al compilar los datos contables: {e}"


@tool
def obtener_reporte_facturacion_semanal() -> str:
    """
    Retorna un reporte ejecutivo para la dueña con los ingresos de la semana actual.
    (Mantenido por retrocompatibilidad).
    """
    return obtener_reporte_facturacion.invoke({"periodo": "semana", "mes_o_fecha": ""})


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

    from .profesores_tools import obtener_profesor_de_turno
    for t in turnos_hoy:
        prof_obj = obtener_profesor_de_turno(t)
        profe = f" - {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        resultado.append(f"• {t.hora_inicio.strftime('%H:%M')} hs: {3 - t.cupo_actual}/3 ocupadas{profe}")

    return "\n".join(resultado)


@tool
def obtener_reporte_ocupacion_mes(mes_o_fecha: str = "") -> str:
    """
    Retorna a la dueña (Deby) la métrica mensual de ocupación: cantidad de clases dictadas,
    cantidad y porcentaje de clases 100% llenas (con todas las camillas cubiertas),
    y el promedio general de ocupación del mes.
    """
    today = timezone.localdate()
    mes = today.month
    year = today.year
    nombre_mes = "mes actual"
    for k, v in MESES_MAP.items():
        if k in mes_o_fecha.lower():
            mes = v
            nombre_mes = k.capitalize()
            break

    turnos_mes = Turno.objects.filter(
        fecha__month=mes,
        fecha__year=year,
        estado__in=['PROGRAMADO', 'COMPLETADO', 'REALIZADO']
    ).select_related('clase').prefetch_related('reservas')

    total_clases = turnos_mes.count()
    if total_clases == 0:
        return f"No hay registros de clases dictadas en {nombre_mes}."

    clases_llenas = 0
    ocupacion_acumulada = 0
    for t in turnos_mes:
        cap = t.clase.cupo_maximo
        res_activas = sum(1 for r in t.reservas.all() if r.estado in ['CONFIRMADA', 'TOMADA', 'AUSENTE'])
        ocupados = max(cap - t.cupo_actual, res_activas)
        if cap > 0:
            ocupacion_acumulada += min(1.0, ocupados / cap)
            if t.cupo_actual <= 0 or ocupados >= cap:
                clases_llenas += 1

    pct_llenas = round((clases_llenas / total_clases) * 100) if total_clases > 0 else 0
    pct_promedio = round((ocupacion_acumulada / total_clases) * 100) if total_clases > 0 else 0

    return (
        f"✦ Métricas de Ocupación ({nombre_mes} {year}):\n"
        f"• Clases 100% llenas: {clases_llenas} de {total_clases} ({pct_llenas}% de clases al máximo)\n"
        f"• Ocupación promedio de camillas: {pct_promedio}%\n"
        f"• Clases con camillas libres: {total_clases - clases_llenas} clases"
    )


@tool
def contactar_prospectos_desde_lista(texto_con_contactos: str) -> str:
    """
    Permite a la dueña pasar una lista o texto con números de teléfono de interesadas
    para que el asistente les envíe un primer mensaje cálido de bienvenida e invitación a Violett Pilates.
    """
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
