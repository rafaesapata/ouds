"""
Utilitários para o sistema de conhecimento.
Este módulo fornece funções auxiliares para o sistema de conhecimento,
evitando importações circulares.
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def get_knowledge_manager():
    """
    Obtém uma instância do KnowledgeManager de forma segura,
    evitando importações circulares.
    
    Returns:
        Instância do KnowledgeManager ou None em caso de erro
    """
    try:
        from app.knowledge.workspace_knowledge import KnowledgeManager
        return KnowledgeManager()
    except Exception as e:
        logger.error(f"Erro ao obter KnowledgeManager: {e}")
        return None

async def get_knowledge_context(message: str, workspace_id: str = "default", limit: int = 5) -> str:
    """
    Obtém contexto de conhecimento para uma mensagem.
    
    Args:
        message: Mensagem do usuário
        workspace_id: ID do workspace
        limit: Número máximo de entradas de conhecimento a retornar
        
    Returns:
        String com o contexto de conhecimento relevante
    """
    try:
        # Obter KnowledgeManager
        knowledge_manager = get_knowledge_manager()
        if not knowledge_manager:
            return ""
        
        # Buscar conhecimento relevante do workspace
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=limit)
        
        # Construir contexto
        if relevant_knowledge:
            context = "Conhecimento específico do workspace:\n"
            for entry in relevant_knowledge:
                context += f"- {entry.content}\n"
                # Atualizar estatísticas de uso
                knowledge_manager.update_knowledge_usage(workspace_id, entry.id)
            
            logger.info(f"Conhecimento do workspace obtido: {len(relevant_knowledge)} entradas")
            return context
        
        return ""
        
    except Exception as e:
        logger.error(f"Erro ao obter contexto de conhecimento: {e}")
        return ""

async def get_file_context(message: str, workspace_id: str = "default") -> str:
    """
    Obtém contexto de arquivos para uma mensagem.
    
    Args:
        message: Mensagem do usuário
        workspace_id: ID do workspace
        
    Returns:
        String com o contexto de arquivos relevante
    """
    try:
        from app.knowledge.file_integration import get_file_context_for_chat
        
        # Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        
        if file_context:
            logger.info("Contexto de arquivos obtido")
            return f"Informações de arquivos do workspace:\n{file_context}"
        
        return ""
        
    except Exception as e:
        logger.error(f"Erro ao obter contexto de arquivos: {e}")
        return ""

