from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Historial de mensajes de la conversación
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Contexto del usuario y del negocio
    conversacion_id: str
    phone: str
    rol: str # ALUMNA, PROFESOR, DUENA, PROSPECTO
    usuario_id: Optional[str]
    nombre_usuario: Optional[str]
    
    # Orquestación y auditoría
    next_node: str # Nombre del siguiente agente o END
    agente_responsable: str
    tools_usadas: List[str]
    esperando_humano: bool
