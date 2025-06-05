"""
OUDS - Módulo de Base de Conhecimento por Workspace
=================================================

Este módulo integra todos os componentes do sistema de conhecimento:
- Gerenciamento de conhecimento por workspace
- Roteamento inteligente de múltiplas LLMs
- Evolução e aprendizado contínuo
"""

from .workspace_knowledge import knowledge_manager, KnowledgeEntry, ConversationRecord
from .llm_router import llm_router, ContextType, LLMProvider
from .evolution_engine import evolution_engine

__version__ = "1.0.0"
__all__ = [
    "knowledge_manager",
    "llm_router", 
    "evolution_engine",
    "KnowledgeEntry",
    "ConversationRecord",
    "ContextType",
    "LLMProvider"
]

