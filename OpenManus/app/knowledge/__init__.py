"""
Módulo de conhecimento para o sistema OUDS.
Este módulo fornece funcionalidades para gerenciar e acessar
a base de conhecimento do sistema.
"""

# Importações para facilitar o acesso a funcionalidades comuns
try:
    from app.knowledge.global_knowledge import get_system_context_for_llm
except ImportError:
    import logging
    logging.getLogger(__name__).error("Falha ao importar get_system_context_for_llm")

try:
    from app.knowledge.workspace_knowledge import KnowledgeManager
    # Instância global do gerenciador de conhecimento
    knowledge_manager = KnowledgeManager()
except ImportError:
    import logging
    logging.getLogger(__name__).error("Falha ao importar KnowledgeManager")

# Definição de tipos de dados
class ConversationRecord:
    """Registro de uma conversa entre usuário e assistente."""
    
    def __init__(self, id, timestamp, user_message, assistant_response, 
                 llm_used=None, context_retrieved=None, knowledge_learned=None,
                 processing_time=None):
        self.id = id
        self.timestamp = timestamp
        self.user_message = user_message
        self.assistant_response = assistant_response
        self.llm_used = llm_used or "unknown"
        self.context_retrieved = context_retrieved or []
        self.knowledge_learned = knowledge_learned or []
        self.processing_time = processing_time or 0.0
    
    def to_dict(self):
        """Converte o registro para um dicionário."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "llm_used": self.llm_used,
            "context_retrieved": self.context_retrieved,
            "knowledge_learned": self.knowledge_learned,
            "processing_time": self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria um registro a partir de um dicionário."""
        return cls(
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            user_message=data.get("user_message"),
            assistant_response=data.get("assistant_response"),
            llm_used=data.get("llm_used"),
            context_retrieved=data.get("context_retrieved"),
            knowledge_learned=data.get("knowledge_learned"),
            processing_time=data.get("processing_time")
        )

