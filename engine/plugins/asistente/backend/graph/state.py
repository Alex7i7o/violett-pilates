from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    # Historial de mensajes de la conversación
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Contexto del usuario y del negocio
    conversacion_id: str
    phone: str
    rol: str # ALUMNA, PROFESOR, DUENA, PROSPECTO
    usuario_id: Optional[str]
    nombre_usuario: Optional[str]
    
    # Orquestación y auditoría
    target_agent: Optional[str] # agente_turnos, agente_finanzas, agente_profesores, agente_direccion, agente_recepcionista
    next_node: str
    agente_responsable: str
    tools_usadas: List[str]
    esperando_humano: bool
