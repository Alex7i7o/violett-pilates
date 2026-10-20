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

    return f"""✦ Estado de tu Plan:
• Plan: {sub.plan.nombre}
• Créditos disponibles para reservar: {sub.clases_restantes}
• Vencimiento: {sub.fecha_vencimiento.strftime('%d/%m/%Y')}
• Estado: {estado_str}"""


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
    """
    config = get_asistente_config()
    reglas = config.get('reglas_operativas', {})
    alias = reglas.get('alias_transferencia', 'VIOLETT.PILATES')
    titular = reglas.get('titular_transferencia', 'Débora Zárate')

    return f"""✦ Datos oficiales para transferencia bancaria:
• Alias: {alias}
• Titular: {titular}

Una vez realizada la transferencia, podés enviarme la foto del comprobante directamente por acá para acreditar tus clases ✦."""
