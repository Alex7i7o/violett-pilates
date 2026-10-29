import datetime
import logging
from django.utils import timezone
from langchain_core.tools import tool

from core.models import Usuario
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

@tool
def consultar_estado_plan_alumna(usuario_id: str) -> str:
    """
    Consulta los detalles del abono o membresía activa de una alumna:
    nombre del plan, clases restantes disponibles, clases ya agendadas y fecha de vencimiento.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema."

    try:
        from plugins.membresias.backend.models import Suscripcion
    except ImportError:
        return "El módulo de membresías no está habilitado."

    sub = Suscripcion.objects.filter(
        usuario_id=usuario_id,
        estado__in=['ACTIVO', 'AGOTADO']
    ).select_related('plan').order_by('-fecha_inicio').first()

    if not sub:
        return "Actualmente no tenés ningún plan activo registrado. ¿Te gustaría conocer los planes disponibles para comenzar?"

    vencido = sub.fecha_vencimiento < timezone.localdate()
    estado_str = "Vencido" if vencido else ("Agotado (Clases ya agendadas)" if sub.clases_restantes == 0 else "Activo")

    return f"""✦ Información de la membresía:
• Plan: {sub.plan.nombre}
• Créditos disponibles para reservar turnos: {sub.clases_restantes}
• Vencimiento del abono: {sub.fecha_vencimiento.strftime('%d/%m/%Y')}
• Estado: {estado_str}
(Nota: Si tiene 0 créditos disponibles, ya tiene todas sus clases agendadas o consumidas de este mes, por lo que no puede reservar otra clase sin sumar una clase extra o renovar)."""


@tool
def obtener_planes_y_precios() -> str:
    """
    Retorna la lista de planes de Pilates Reformer disponibles, cantidad de clases mensuales y precios.
    """
    try:
        from plugins.membresias.backend.models import Plan
        planes = Plan.objects.filter(is_active=True).order_by('cantidad_clases')
    except ImportError:
        return "Los planes no están disponibles en este momento."

    if not planes.exists():
        return "No hay planes configurados actualmente."

    resultado = ["✦ Planes disponibles en Violett Pilates:"]
    for p in planes:
        precio_str = f"${p.precio:,.0f}".replace(",", ".") if hasattr(p, 'precio') and p.precio else "Consultar"
        resultado.append(f"• {p.nombre}: {p.cantidad_clases} clases mensuales por {precio_str} (Vigencia 30 días)")

    resultado.append("\nEl plan más elegido por nuestra comunidad es el de 8 clases mensuales (2 veces por semana) ✦.")
    return "\n".join(resultado)


@tool
def obtener_datos_transferencia_estudio() -> str:
    """
    Retorna los datos bancarios oficiales del estudio para transferencias (Alias, CBU, Titular).
    Si no están cargados en el sistema, informa honestamente que se consultará con la administración.
    NUNCA inventes un alias si no está configurado.
    """
    config = get_asistente_config()
    reglas = config.get('reglas_operativas', {})
    alias = reglas.get('alias_transferencia', '').strip()
    titular = reglas.get('titular_transferencia', '').strip()

    if not alias or alias.upper() in ['VIOLETT.PILATES', 'CONSULTAR', 'A_DEFINIR']:
        # Alertar a la dueña si está configurado su teléfono
        tel_duena = config.get('telefono_duena')
        if tel_duena:
            try:
                from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
                WhatsAppClient().send_text_message(
                    tel_duena,
                    "✦ [ALERTA ASISTENTE]: Una clienta solicitó los datos de transferencia/alias bancario, pero aún no están cargados en la configuración oficial del sistema."
                )
            except Exception:
                pass
        return "Actualmente no tengo registrado el alias bancario oficial en el sistema. Ya le dejé un aviso a Débora (dueña del estudio) para que te lo facilitemos a la brevedad ✦."

    lineas = ["✦ Datos oficiales para transferencia bancaria:"]
    lineas.append(f"• Alias: {alias}")
    if titular:
        lineas.append(f"• Titular: {titular}")
    lineas.append("\nUna vez realizada la transferencia, podés enviarme la foto del comprobante directamente por acá para acreditar tus clases ✦.")
    return "\n".join(lineas)


@tool
def consultar_a_la_duena(pregunta_o_motivo: str, remitente_info: str = "") -> str:
    """
    Envía una consulta o duda urgente directamente a la dueña del estudio (Débora) por WhatsApp
    cuando una alumna o interesada pregunta algo que no figura en la base de datos ni en las reglas oficiales.
    NUNCA inventes información. Si no sabés, usá esta herramienta.
    """
    config = get_asistente_config()
    tel_duena = config.get('telefono_duena')
    if not tel_duena:
        return "Disculpá, en este momento no pude derivar la consulta automáticamente. En breve una recepcionista te responderá."

    try:
        from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
        remitente_str = f" de {remitente_info}" if remitente_info else ""
        msg = f"✦ [CONSULTA DERIVADA POR ASISTENTE]{remitente_str}:\n'{pregunta_o_motivo}'\n\nPodés responderle directamente o indicarme qué informarle."
        WhatsAppClient().send_text_message(tel_duena, msg)
        return "✦ Ya le envié tu consulta a Débora (dueña del estudio) para confirmarte con exactitud. En cuanto nos indique, te avisamos por acá."
    except Exception as e:
        logger.error(f"Error derivando consulta a dueña: {e}")
        return "✦ Dejame registrada tu consulta para transmitírsela a la dueña a la brevedad."


@tool
def aprobar_comprobante_pago(identificador: str = "") -> str:
    """
    Comando administrativo para la dueña / administración del estudio.
    Aprueba un comprobante de pago pendiente, acredita el plan a la alumna en la base de datos,
    dispara el auto-agendamiento de turnos recurrentes fijos y notifica a la alumna por WhatsApp.
    Parámetro 'identificador': Código hexadecimal del comprobante (ej: '953e69') o nombre de la alumna.
    Si se deja vacío, toma el comprobante pendiente más reciente.
    """
    from ..models import ComprobantePendiente, RegistroAccionIA, MensajeWhatsAppLog
    from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
    from plugins.membresias.backend.models import Plan, Suscripcion
    from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario

    qs = ComprobantePendiente.objects.filter(estado='PENDIENTE').order_by('-created_at')
    
    comp = None
    if identificador:
        id_clean = identificador.strip().lower()
        # Buscar por prefijo UUID
        for c in qs:
            if c.id.hex.startswith(id_clean):
                comp = c
                break
        
        # Si no se encontró por ID, buscar por nombre de usuario o emisor
        if not comp:
            comp = qs.filter(
                usuario__nombre__icontains=id_clean
            ).first() or qs.filter(
                usuario__apellido__icontains=id_clean
            ).first() or qs.filter(
                datos_extraidos__emisor__icontains=id_clean
            ).first()

    if not comp:
        # Tomar el más reciente
        comp = qs.first()

    if not comp:
        return "No hay ningún comprobante de pago pendiente de aprobación en este momento."

    # Vincular usuario si aún no estaba vinculado
    usuario = comp.usuario
    if not usuario and comp.conversacion:
        usuario = comp.conversacion.usuario
        if not usuario:
            tel_8 = comp.conversacion.telefono[-8:]
            usuario = Usuario.objects.filter(telefono__icontains=tel_8).first()
        if usuario:
            comp.usuario = usuario

    if not usuario:
        return f"El comprobante #{comp.id.hex[:6]} no tiene un usuario de Violett Pilates asociado. Por favor vinculalo primero."

    # Identificar o buscar Plan
    plan = None
    if comp.plan_id:
        plan = Plan.objects.filter(id=comp.plan_id).first()
    if not plan and comp.monto:
        plan = Plan.objects.filter(is_active=True, precio=comp.monto).first()
    if not plan:
        plan = Plan.objects.filter(is_active=True).order_by('-cantidad_clases').first()

    if not plan:
        return f"No se encontró un plan activo compatible para el monto ${comp.monto}."

    # Crear o renovar suscripción
    hoy = timezone.localdate()
    vencimiento = hoy + datetime.timedelta(days=30)
    
    sub = Suscripcion.objects.create(
        usuario=usuario,
        plan=plan,
        fecha_inicio=hoy,
        fecha_vencimiento=vencimiento,
        clases_restantes=plan.cantidad_clases,
        estado='ACTIVO'
    )

    # Auto-agendar turnos fijos semanales si la alumna tiene recurrencias configuradas
    reservas_creadas = 0
    try:
        reservas_creadas = auto_agendar_recurrencias_usuario(usuario, sub)
    except Exception as e:
        logger.error(f"Error auto-agendando recurrencias al aprobar pago: {e}")

    # Marcar comprobante como APROBADO
    comp.estado = 'APROBADO'
    comp.plan_nombre = plan.nombre
    comp.save()

    # Notificar a la alumna vía WhatsApp
    nombre_alumna = usuario.nombre or "Alumna"
    clean_phone = comp.conversacion.telefono
    client = WhatsAppClient()
    
    monto_fmt = f"${comp.monto:,.0f}".replace(",", ".") if comp.monto else ""
    monto_txt = f" por {monto_fmt}" if monto_fmt else ""
    
    msg_alumna = (
        f"✦ ¡Buenas noticias {nombre_alumna}! Tu transferencia{monto_txt} ({plan.nombre}) fue acreditada.\n\n"
        f"Ya tenés tus {sub.clases_restantes} clases disponibles con vigencia hasta el {vencimiento.strftime('%d/%m/%Y')}."
    )
    if reservas_creadas > 0:
        msg_alumna += f"\n\nAdemás, te aseguramos automáticamente tus {reservas_creadas} turnos fijos de la semana ✦."
    else:
        msg_alumna += "\n\nPodés escribirme en cualquier momento para consultar turnos y reservar tu camilla ✦."

    try:
        client.send_text_message(clean_phone, msg_alumna)
        MensajeWhatsAppLog.objects.create(
            conversacion=comp.conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_finanzas_aprobacion',
            texto=msg_alumna
        )
    except Exception as e:
        logger.warning(f"No se pudo enviar WhatsApp a alumna {clean_phone}: {e}")

    # Registrar acción de IA
    RegistroAccionIA.objects.create(
        conversacion=comp.conversacion,
        tipo_accion='PLAN_REACTIVADO',
        descripcion=f"Comprobante #{comp.id.hex[:6]} aprobado. Plan {plan.nombre} acreditado para {usuario.email}. Clases: {plan.cantidad_clases}, Recurrencias autoagendadas: {reservas_creadas}.",
        payload={'comprobante_id': str(comp.id), 'usuario_id': str(usuario.id), 'monto': float(comp.monto or 0), 'reservas_creadas': reservas_creadas}
    )

    return f"✅ ¡Comprobante #{comp.id.hex[:6]} aprobado con éxito!\n• Alumna: *{nombre_alumna}* ({clean_phone})\n• Plan acreditado: *{plan.nombre}* ({plan.cantidad_clases} clases)\n• Turnos fijos agendados automáticamente: *{reservas_creadas}*\n• Alumna notificada por WhatsApp."


@tool
def rechazar_comprobante_pago(identificador: str = "", motivo: str = "") -> str:
    """
    Comando administrativo para la dueña / administración del estudio.
    Rechaza un comprobante de pago pendiente y le avisa con cordialidad a la alumna
    indicando el motivo para que pueda reenviarlo o revisarlo.
    """
    from ..models import ComprobantePendiente, RegistroAccionIA, MensajeWhatsAppLog
    from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient

    qs = ComprobantePendiente.objects.filter(estado='PENDIENTE').order_by('-created_at')
    comp = None
    if identificador:
        id_clean = identificador.strip().lower()
        for c in qs:
            if c.id.hex.startswith(id_clean):
                comp = c
                break
        if not comp:
            comp = qs.filter(usuario__nombre__icontains=id_clean).first()

    if not comp:
        comp = qs.first()

    if not comp:
        return "No hay ningún comprobante de pago pendiente para rechazar."

    comp.estado = 'RECHAZADO'
    comp.save()

    nombre_alumna = comp.usuario.nombre if comp.usuario and comp.usuario.nombre else "Alumna"
    clean_phone = comp.conversacion.telefono
    client = WhatsAppClient()

    motivo_texto = motivo.strip() if motivo else "no pudimos verificar el ingreso del monto en la cuenta bancaria"

    msg_alumna = (
        f"¡Hola {nombre_alumna}! ✦ Te escribimos desde Violett Pilates.\n\n"
        f"Revisamos tu comprobante pero tuvimos la siguiente dificultad: {motivo_texto}.\n\n"
        f"¿Podrías por favor verificar la operación en tu app bancaria o reenviarnos una foto clara del comprobante? ¡Muchas gracias!"
    )

    try:
        client.send_text_message(clean_phone, msg_alumna)
        MensajeWhatsAppLog.objects.create(
            conversacion=comp.conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_finanzas_rechazo',
            texto=msg_alumna
        )
    except Exception as e:
        logger.warning(f"No se pudo enviar WhatsApp a alumna {clean_phone}: {e}")

    return f"❌ Comprobante #{comp.id.hex[:6]} rechazado. Se le envió un mensaje a la alumna solicitando regularizar la situación."
