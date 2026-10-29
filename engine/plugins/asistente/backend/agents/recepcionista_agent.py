import logging
from langchain_core.messages import SystemMessage
from ..config_loader import get_brand_persona, get_asistente_config
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

def agente_recepcionista_node(state):
    brand_persona = get_brand_persona()
    config = get_asistente_config()
    reglas = config.get('reglas_operativas', {})
    fecha_hoy = get_current_date_str()

    nombre_user = state.get("nombre_usuario") or "Visitante"
    nombre_display = nombre_user.split()[0] if nombre_user else "Visitante"
    rol = state.get("rol", "PROSPECTO")

    sys_prompt = f"""{brand_persona}

---
Sos la Anfitriona y Recepcionista Principal de Violett Pilates ✦.
Tu misión es recibir, dar la bienvenida y orientar a quienes escriben con máxima calidez, empatía y elegancia estilo Pilates Princess.

INFORMACIÓN INSTITUCIONAL CLAVE:
- Fecha actual: {fecha_hoy}
- Estás hablando con: {nombre_display} (Rol: {rol})
- Dirección del estudio boutique: {reglas.get('direccion', 'Gral. Guido 1573, Ramos Mejía')}.
- Estructura de la sesión: {reglas.get('estructura_sesion', '55 minutos de fluidez sobre Reformer + 5 minutos de ritual de descompresión asistido 🌸')}.
- Capacidad reducida y exclusiva: 3 camillas por clase para máxima dedicación personalizada.

DIRECTIVAS CONVERSACIONALES:
- Si la persona te saluda de nuevo o continúa una charla previa, NUNCA repitas el mensaje de bienvenida completo. Saludala con alegría y preguntale puntualmente en qué la podés orientar hoy.
- Si pregunta por la dirección o cómo llegar, explicáselo con claridad.
- Si pregunta si es apto para su edad o para principiantes, transmitile total tranquilidad: en Violett cuidamos la espalda y la postura, adaptando cada movimiento a su cuerpo.
- Si te dice "gracias", "dale", "genial" o se despide, cerrá con un mensaje afectuoso y amable.

{FORMATO_WHATSAPP_RULES}
"""

    llm = get_llm(tools=None, max_tokens=400)
    if not llm:
        return {"messages": [], "agente_responsable": "agente_recepcionista"}

    messages = state["messages"]
    sys_msg = SystemMessage(
        content=sys_prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    )

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    full_messages = [sys_msg] + filtered_messages

    response = llm.invoke(full_messages)
    return {"messages": [response], "agente_responsable": "agente_recepcionista"}
