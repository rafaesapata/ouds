"""
OUDS - APIs do Sistema de Conhecimento para FastAPI
=================================================

APIs para gerenciamento de conhecimento por workspace,
múltiplas LLMs e evolução automática adaptadas para FastAPI.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
import logging

from app.knowledge import (
    knowledge_manager, 
    llm_router, 
    evolution_engine,
    KnowledgeEntry,
    ConversationRecord,
    ContextType,
    LLMProvider
)

logger = logging.getLogger(__name__)

# Modelos Pydantic para as APIs
class AddKnowledgeRequest(BaseModel):
    content: str
    type: str = "fact"
    source: str = "manual"
    confidence: float = 1.0
    tags: List[str] = []

class SearchKnowledgeRequest(BaseModel):
    query: str
    limit: int = 10

class ProcessConversationRequest(BaseModel):
    conversation: Dict[str, Any]

class LLMRouteRequest(BaseModel):
    message: str
    workspace_id: str = "default"
    conversation_history: List[Dict] = []

class LLMCallRequest(BaseModel):
    provider: str
    messages: List[Dict]
    workspace_id: str = "default"

class CleanupRequest(BaseModel):
    days_threshold: int = 90

# Router para APIs de conhecimento
knowledge_router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

@knowledge_router.post("/workspace/{workspace_id}/add")
async def add_knowledge(workspace_id: str, request: AddKnowledgeRequest):
    """Adiciona conhecimento a um workspace"""
    try:
        # Criar entrada de conhecimento
        entry = KnowledgeEntry.create(
            content=request.content,
            type=request.type,
            source=request.source,
            confidence=request.confidence,
            tags=request.tags
        )
        
        # Adicionar à base de conhecimento
        success = knowledge_manager.add_knowledge(workspace_id, entry)
        
        if success:
            return {
                'success': True,
                'knowledge_id': entry.id,
                'message': 'Conhecimento adicionado com sucesso'
            }
        else:
            raise HTTPException(status_code=500, detail='Erro ao adicionar conhecimento')
            
    except Exception as e:
        logger.error(f"Erro ao adicionar conhecimento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/workspace/{workspace_id}/search")
async def search_knowledge(workspace_id: str, q: str, limit: int = 10):
    """Busca conhecimento em um workspace"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail='Query é obrigatória')
        
        # Buscar conhecimento
        results = knowledge_manager.search_knowledge(workspace_id, q, limit)
        
        # Converter para dicionários
        results_data = [
            {
                'id': entry.id,
                'type': entry.type,
                'content': entry.content,
                'confidence': entry.confidence,
                'source': entry.source,
                'created_at': entry.created_at,
                'last_used': entry.last_used,
                'usage_count': entry.usage_count,
                'tags': entry.tags
            }
            for entry in results
        ]
        
        return {
            'success': True,
            'results': results_data,
            'total': len(results_data)
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar conhecimento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.get("/workspace/{workspace_id}/stats")
async def get_workspace_stats(workspace_id: str):
    """Retorna estatísticas do workspace"""
    try:
        stats = knowledge_manager.get_workspace_stats(workspace_id)
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@knowledge_router.post("/workspace/{workspace_id}/cleanup")
async def cleanup_workspace(workspace_id: str, request: CleanupRequest):
    """Limpa conhecimento antigo do workspace"""
    try:
        removed_count = knowledge_manager.cleanup_old_knowledge(workspace_id, request.days_threshold)
        
        return {
            'success': True,
            'removed_count': removed_count,
            'message': f'Removidas {removed_count} entradas antigas'
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Router para APIs de LLMs
llm_router_api = APIRouter(prefix="/api/llm", tags=["llm"])

@llm_router_api.get("/available")
async def get_available_llms():
    """Lista LLMs disponíveis"""
    try:
        stats = llm_router.get_performance_stats()
        return {
            'success': True,
            'llms': stats
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter LLMs disponíveis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@llm_router_api.post("/route")
async def route_llm_request(request: LLMRouteRequest):
    """Roteia requisição para LLM apropriada"""
    try:
        # Classificar contexto
        context_type = llm_router.classify_context(request.message, request.conversation_history)
        
        # Selecionar LLM
        selected_llm, confidence = llm_router.select_llm(context_type, request.workspace_id)
        
        return {
            'success': True,
            'selected_llm': selected_llm.value,
            'context_type': context_type.value,
            'confidence': confidence
        }
        
    except Exception as e:
        logger.error(f"Erro ao rotear LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@llm_router_api.post("/call")
async def call_llm(request: LLMCallRequest):
    """Chama uma LLM específica"""
    try:
        provider = LLMProvider(request.provider)
        
        # Chamar LLM
        response = await llm_router.call_llm(provider, request.messages, request.workspace_id)
        
        return {
            'success': True,
            'response': response
        }
        
    except Exception as e:
        logger.error(f"Erro ao chamar LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@llm_router_api.get("/stats")
async def get_llm_stats():
    """Retorna estatísticas das LLMs"""
    try:
        stats = llm_router.get_performance_stats()
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas das LLMs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Router para APIs de evolução
evolution_router = APIRouter(prefix="/api/evolution", tags=["evolution"])

@evolution_router.post("/workspace/{workspace_id}/process")
async def process_conversation_for_learning(workspace_id: str, request: ProcessConversationRequest):
    """Processa conversa para aprendizado"""
    try:
        conv_data = request.conversation
        
        # Criar registro de conversa
        conversation = ConversationRecord(
            id=conv_data.get('id', f"conv_{datetime.now().timestamp()}"),
            timestamp=conv_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            user_message=conv_data['user_message'],
            assistant_response=conv_data['assistant_response'],
            llm_used=conv_data.get('llm_used', 'unknown'),
            context_retrieved=conv_data.get('context_retrieved', []),
            knowledge_learned=conv_data.get('knowledge_learned', []),
            satisfaction_score=conv_data.get('satisfaction_score'),
            processing_time=conv_data.get('processing_time')
        )
        
        # Processar para aprendizado
        await evolution_engine.process_conversation(conversation, workspace_id)
        
        # Adicionar ao histórico
        knowledge_manager.add_conversation(workspace_id, conversation)
        
        return {
            'success': True,
            'message': 'Conversa processada para aprendizado'
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@evolution_router.get("/workspace/{workspace_id}/insights")
async def get_evolution_insights(workspace_id: str):
    """Retorna insights de evolução do workspace"""
    try:
        insights = await evolution_engine.analyze_workspace_evolution(workspace_id)
        
        insights_data = [
            {
                'insight_type': insight.insight_type,
                'description': insight.description,
                'confidence': insight.confidence,
                'supporting_evidence': insight.supporting_evidence,
                'recommended_action': insight.recommended_action
            }
            for insight in insights
        ]
        
        return {
            'success': True,
            'insights': insights_data
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@evolution_router.post("/workspace/{workspace_id}/cleanup-patterns")
async def cleanup_learning_patterns(workspace_id: str, request: CleanupRequest):
    """Limpa padrões de aprendizado antigos"""
    try:
        removed_count = await evolution_engine.cleanup_learning_patterns(workspace_id, request.days_threshold)
        
        return {
            'success': True,
            'removed_count': removed_count,
            'message': f'Removidos {removed_count} padrões antigos'
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar padrões: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Função para registrar routers
def register_knowledge_routers(app):
    """Registra todos os routers do sistema de conhecimento"""
    app.include_router(knowledge_router)
    app.include_router(llm_router_api)
    app.include_router(evolution_router)
    
    logger.info("Routers do sistema de conhecimento registrados")

# Função para inicializar sistema de conhecimento
def initialize_knowledge_system():
    """Inicializa o sistema de conhecimento"""
    try:
        # Criar diretórios necessários
        import os
        os.makedirs("/home/ubuntu/ouds-project/workspace_knowledge", exist_ok=True)
        os.makedirs("/home/ubuntu/ouds-project/OpenManus/config", exist_ok=True)
        
        logger.info("Sistema de conhecimento inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar sistema de conhecimento: {e}")
        return False

