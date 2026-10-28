import os
import logging
from typing import List, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)

FORMATO_WHATSAPP_RULES = """REGLAS ESTRICTAS DE FORMATO NATIVO PARA WHATSAPP:
- Estás respondiendo en WhatsApp. NUNCA uses encabezados de Markdown con hashtags (`#`, `##`, `###`, `####`). Están TERMINANTEMENTE PROHIBIDOS.
- NUNCA uses tablas de Markdown con barras verticales (`| col | col |` o `|---|---|`). Están TERMINANTEMENTE PROHIBIDAS porque en celular se ven rotas e ilegibles.
- En WhatsApp la negrita se escribe con UN SOLO ASTERISCO `*texto*`. NUNCA uses doble asterisco `**texto**`.
- Mostrá listas con viñetas limpias usando el destello `✦` o puntos `•`.
- Usá siempre voseo argentino cordial, cálido y elegante ('vos', 'querés', 'fijate', 'sentite').
- NUNCA expongas IDs numéricos internos de base de datos a las alumnas ni a la clientela.
"""

def get_llm(tools: Optional[List] = None, temperature: float = 0.3, max_tokens: int = 600):
    """
    Crea la instancia de LLM compartida con parámetros optimizados de velocidad y baja latencia.
    Prioridad: Anthropic (Haiku) > OpenAI (gpt-4o-mini) > Groq (llama-3.3-70b)
    """
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')

    llm = None

    if anthropic_key:
        from langchain_anthropic import ChatAnthropic
        model_name = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022')
        llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=anthropic_key
        )
    elif openai_key:
        from langchain_openai import ChatOpenAI
        model_name = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=openai_key
        )
    elif groq_key:
        from langchain_groq import ChatGroq
        model_name = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
        llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=groq_key
        )

    if llm and tools:
        llm = llm.bind_tools(tools)

    return llm

def get_current_date_str() -> str:
    return timezone.localdate().strftime('%A %d de %B de %Y')
