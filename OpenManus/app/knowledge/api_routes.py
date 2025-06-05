"""
OUDS - APIs do Sistema de Conhecimento
====================================

APIs para gerenciamento de conhecimento por workspace,
múltiplas LLMs e evolução automática.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
import asyncio
import logging
from typing import Dict, Any, List

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

# Blueprint para as APIs de conhecimento
knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

@knowledge_bp.route('/workspace/<workspace_id>/add', methods=['POST'])
def add_knowledge(workspace_id: str):
    """Adiciona conhecimento a um workspace"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'content' not in data:
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        # Criar entrada de conhecimento
        entry = KnowledgeEntry.create(
            content=data['content'],
            type=data.get('type', 'fact'),
            source=data.get('source', 'manual'),
            confidence=data.get('confidence', 1.0),
            tags=data.get('tags', [])
        )
        
        # Adicionar à base de conhecimento
        success = knowledge_manager.add_knowledge(workspace_id, entry)
        
        if success:
            return jsonify({
                'success': True,
                'knowledge_id': entry.id,
                'message': 'Conhecimento adicionado com sucesso'
            })
        else:
            return jsonify({'error': 'Erro ao adicionar conhecimento'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao adicionar conhecimento: {e}")
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/workspace/<workspace_id>/search', methods=['GET'])
def search_knowledge(workspace_id: str):
    """Busca conhecimento em um workspace"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'error': 'Query é obrigatória'}), 400
        
        # Buscar conhecimento
        results = knowledge_manager.search_knowledge(workspace_id, query, limit)
        
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
        
        return jsonify({
            'success': True,
            'results': results_data,
            'total': len(results_data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar conhecimento: {e}")
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/workspace/<workspace_id>/stats', methods=['GET'])
def get_workspace_stats(workspace_id: str):
    """Retorna estatísticas do workspace"""
    try:
        stats = knowledge_manager.get_workspace_stats(workspace_id)
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/workspace/<workspace_id>/cleanup', methods=['POST'])
def cleanup_workspace(workspace_id: str):
    """Limpa conhecimento antigo do workspace"""
    try:
        data = request.get_json() or {}
        days_threshold = data.get('days_threshold', 90)
        
        removed_count = knowledge_manager.cleanup_old_knowledge(workspace_id, days_threshold)
        
        return jsonify({
            'success': True,
            'removed_count': removed_count,
            'message': f'Removidas {removed_count} entradas antigas'
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar workspace: {e}")
        return jsonify({'error': str(e)}), 500

# APIs do Sistema de LLMs
llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

@llm_bp.route('/available', methods=['GET'])
def get_available_llms():
    """Lista LLMs disponíveis"""
    try:
        stats = llm_router.get_performance_stats()
        return jsonify({
            'success': True,
            'llms': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter LLMs disponíveis: {e}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/route', methods=['POST'])
def route_llm_request():
    """Roteia requisição para LLM apropriada"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        message = data['message']
        workspace_id = data.get('workspace_id', 'default')
        conversation_history = data.get('conversation_history', [])
        
        # Classificar contexto
        context_type = llm_router.classify_context(message, conversation_history)
        
        # Selecionar LLM
        selected_llm, confidence = llm_router.select_llm(context_type, workspace_id)
        
        return jsonify({
            'success': True,
            'selected_llm': selected_llm.value,
            'context_type': context_type.value,
            'confidence': confidence
        })
        
    except Exception as e:
        logger.error(f"Erro ao rotear LLM: {e}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/call', methods=['POST'])
async def call_llm():
    """Chama uma LLM específica"""
    try:
        data = request.get_json()
        
        if not data or 'provider' not in data or 'messages' not in data:
            return jsonify({'error': 'Provider e messages são obrigatórios'}), 400
        
        provider = LLMProvider(data['provider'])
        messages = data['messages']
        workspace_id = data.get('workspace_id', 'default')
        
        # Chamar LLM
        response = await llm_router.call_llm(provider, messages, workspace_id)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        logger.error(f"Erro ao chamar LLM: {e}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/stats', methods=['GET'])
def get_llm_stats():
    """Retorna estatísticas das LLMs"""
    try:
        stats = llm_router.get_performance_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas das LLMs: {e}")
        return jsonify({'error': str(e)}), 500

# APIs do Sistema de Evolução
evolution_bp = Blueprint('evolution', __name__, url_prefix='/api/evolution')

@evolution_bp.route('/workspace/<workspace_id>/process', methods=['POST'])
async def process_conversation_for_learning(workspace_id: str):
    """Processa conversa para aprendizado"""
    try:
        data = request.get_json()
        
        if not data or 'conversation' not in data:
            return jsonify({'error': 'Dados da conversa são obrigatórios'}), 400
        
        conv_data = data['conversation']
        
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
        
        return jsonify({
            'success': True,
            'message': 'Conversa processada para aprendizado'
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar conversa: {e}")
        return jsonify({'error': str(e)}), 500

@evolution_bp.route('/workspace/<workspace_id>/insights', methods=['GET'])
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
        
        return jsonify({
            'success': True,
            'insights': insights_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter insights: {e}")
        return jsonify({'error': str(e)}), 500

@evolution_bp.route('/workspace/<workspace_id>/cleanup-patterns', methods=['POST'])
async def cleanup_learning_patterns(workspace_id: str):
    """Limpa padrões de aprendizado antigos"""
    try:
        data = request.get_json() or {}
        days_threshold = data.get('days_threshold', 30)
        
        removed_count = await evolution_engine.cleanup_learning_patterns(workspace_id, days_threshold)
        
        return jsonify({
            'success': True,
            'removed_count': removed_count,
            'message': f'Removidos {removed_count} padrões antigos'
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar padrões: {e}")
        return jsonify({'error': str(e)}), 500

# Função para registrar blueprints
def register_knowledge_blueprints(app):
    """Registra todos os blueprints do sistema de conhecimento"""
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(evolution_bp)
    
    logger.info("Blueprints do sistema de conhecimento registrados")

# Função para inicializar sistema de conhecimento
def initialize_knowledge_system():
    """Inicializa o sistema de conhecimento"""
    try:
        # Criar diretórios necessários dinamicamente
        try:
            from app.config import config
            knowledge_path = config.workspace_root / "knowledge"
            config_path = config.workspace_root.parent / "config"
        except ImportError:
            # Fallback: usar caminho relativo ao arquivo atual
            from pathlib import Path
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            knowledge_path = project_root / "workspace" / "knowledge"
            config_path = project_root / "config"
        
        knowledge_path.mkdir(parents=True, exist_ok=True)
        config_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Sistema de conhecimento inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar sistema de conhecimento: {e}")
        return False

