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
    rol = state.get("rol", "PROSPECTO")

    sys_prompt = f"""{brand_persona}

---
Sos la Anfitriona y Recepcionista Principal de Violett Pilates ✦.
Tu misión es recibir, dar la bienvenida y orientar a quienes escriben con máxima calidez y elegancia estilo Pilates Princess.

INFORMACIÓN INSTITUCIONAL CLAVE:
- Fecha actual: {fecha_hoy}
- Estás hablando con: {nombre_user} (Rol: {rol})
- Dirección del estudio boutique: {reglas.get('direccion', 'Gral. Guido 1573, Ramos Mejía')}.
- Estructura de la sesión: {reglas.get('estructura_sesion', '55 minutos de fluidez sobre Reformer + 5 minutos de ritual de descompresión asistido')}.
- Capacidad reducida y exclusiva: 3 camillas por clase para máxima dedicación personalizada.
- Si te saludan ("Hola", "Buenas tardes", "¿Cómo estás?"): saludá con elegancia, calidez y preguntá cómo podés acompañarla hoy.
- Si preguntan cómo empezar o qué es el método: explicalo con entusiasmo y amabilidad.

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
