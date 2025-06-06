"""
OUDS - Chat Integrado com Sistema de Conhecimento
===============================================

Versão melhorada do processamento de chat que integra:
- Base de conhecimento por workspace
- Roteamento inteligente de LLMs
- Aprendizado automático
- Acesso a arquivos do workspace
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Rastreamento de saudações por sessão
greeting_sessions = set()

async def get_context_for_chat(message: str, workspace_id: str = "default") -> Optional[str]:
    """
    Obtém contexto relevante para uma mensagem de chat a partir do sistema de conhecimento.
    
    Args:
        message: A mensagem do usuário
        workspace_id: ID do workspace
        
    Returns:
        String com o contexto relevante ou None se não houver contexto
    """
    try:
        # Importar módulos de conhecimento necessários
        from app.knowledge import knowledge_manager
        from app.knowledge.file_integration import get_file_context_for_chat
        
        # Log do workspace sendo usado
        logger.info(f"Obtendo contexto para mensagem no workspace_id: {workspace_id}")
        
        # Buscar conhecimento relevante do workspace
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=5)
        
        # Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        
        # Construir contexto combinado
        combined_context = ""
        
        # Adicionar conhecimento relevante do workspace
        if relevant_knowledge:
            workspace_context = "Conhecimento específico do workspace:\n"
            for entry in relevant_knowledge:
                workspace_context += f"- {entry.content}\n"
                # Atualizar estatísticas de uso
                knowledge_manager.update_knowledge_usage(workspace_id, entry.id)
            
            combined_context += workspace_context
            logger.info(f"Conhecimento do workspace aplicado ao contexto: {len(relevant_knowledge)} entradas")
        
        # Adicionar contexto de arquivos
        if file_context:
            if combined_context:
                combined_context += "\n\n"
            combined_context += f"Informações de arquivos do workspace:\n{file_context}"
            logger.info("Contexto de arquivos aplicado")
        
        # Retornar contexto combinado se existir
        if combined_context:
            logger.info(f"Contexto total: {len(combined_context)} caracteres")
            return combined_context
        else:
            logger.info("Nenhum contexto relevante encontrado")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao obter contexto para chat: {e}")
        return None

async def process_chat_with_knowledge(session_id: str, message: str, workspace_id: str = "default") -> Dict:
    """
    Processa chat com integração completa do sistema de conhecimento
    """
    try:
        # Importar módulos de conhecimento
        from app.knowledge import knowledge_manager, llm_router, evolution_engine, ConversationRecord, get_system_context_for_llm
        from app.knowledge.file_integration import get_file_context_for_chat
        
        # Log do workspace sendo usado
        logger.info(f"Processando chat para workspace_id: {workspace_id}")
        
        # 1. Buscar conhecimento relevante do workspace
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=5)
        
        # Log detalhado do conhecimento encontrado
        if relevant_knowledge:
            logger.info(f"Conhecimento relevante encontrado para '{message[:30]}...': {len(relevant_knowledge)} entradas")
            for i, entry in enumerate(relevant_knowledge):
                logger.info(f"  [{i+1}] {entry.type}: {entry.content[:50]}...")
        else:
            logger.info(f"Nenhum conhecimento relevante encontrado para '{message[:30]}...'")
        
        # 2. Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        if file_context:
            logger.info(f"Contexto de arquivos encontrado para '{message[:30]}...'")
            logger.info(f"Contexto de arquivos: {file_context[:100]}...")
        else:
            logger.info(f"Nenhum contexto de arquivos encontrado para '{message[:30]}...'")
        
        # 3. Classificar contexto e selecionar LLM
        context_type = llm_router.classify_context(message)
        selected_llm, confidence = llm_router.select_llm(context_type, workspace_id)
        
        # 4. Preparar contexto com conhecimento global, do workspace e arquivos
        context_messages = []
        
        # Adicionar conhecimento global do sistema (sempre incluído)
        global_context = get_system_context_for_llm(max_entries=15)
        if global_context:
            # Verificar se já enviamos saudação para esta sessão
            is_first_message = session_id not in greeting_sessions
            
            # Se for a primeira mensagem, usar contexto normal
            # Se não for a primeira mensagem, remover instruções de saudação
            if not is_first_message:
                # Remover instruções de saudação do contexto
                global_context = global_context.replace("O agente deve sempre se apresentar como", "")
                global_context = global_context.replace("deve se apresentar como", "")
                global_context = global_context.replace("deve iniciar com", "")
                global_context = global_context.replace("deve começar com", "")
            
            context_messages.append({
                "role": "system",
                "content": global_context
            })
            
            # Adicionar instrução específica para evitar repetição de saudação
            if not is_first_message:
                context_messages.append({
                    "role": "system",
                    "content": "IMPORTANTE: NÃO repita a frase de saudação. O usuário já foi saudado anteriormente. Responda diretamente à pergunta sem se apresentar novamente."
                })
            
            # Registrar que esta sessão já recebeu saudação
            greeting_sessions.add(session_id)
            
            logger.info("Conhecimento global aplicado ao contexto do chat")
        else:
            logger.warning("Conhecimento global não disponível para o contexto do chat")
        
        # Adicionar contexto combinado (conhecimento do workspace + arquivos)
        combined_context = ""
        
        # Adicionar conhecimento relevante do workspace
        workspace_context = None
        if relevant_knowledge:
            workspace_context = "Conhecimento específico do workspace:\n"
            for entry in relevant_knowledge:
                workspace_context += f"- {entry.content}\n"
                # Atualizar estatísticas de uso
                knowledge_manager.update_knowledge_usage(workspace_id, entry.id)
            
            combined_context += workspace_context
            logger.info("Conhecimento do workspace aplicado ao contexto do chat")
        
        # Adicionar contexto de arquivos
        if file_context:
            if combined_context:
                combined_context += "\n\n"
            combined_context += f"Informações de arquivos do workspace:\n{file_context}"
            logger.info("Contexto de arquivos aplicado ao contexto do chat")
        
        # Adicionar contexto combinado se existir
        if combined_context:
            context_messages.append({
                "role": "system",
                "content": combined_context
            })
        
        # Adicionar mensagem do usuário
        context_messages.append({
            "role": "user", 
            "content": message
        })
        
        # 5. Chamar LLM selecionada
        start_time = datetime.now()
        try:
            llm_response = await llm_router.call_llm(selected_llm, context_messages, workspace_id)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extrair resposta baseada no provedor
            if selected_llm.value.startswith("openai"):
                response_content = llm_response["choices"][0]["message"]["content"]
            elif selected_llm.value.startswith("anthropic"):
                response_content = llm_response["content"][0]["text"]
            else:
                response_content = str(llm_response)
        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
            
            # Fallback para resposta baseada no conhecimento encontrado
            if combined_context:
                # Usar o conhecimento encontrado para gerar uma resposta simples
                response_content = f"Com base no conhecimento disponível:\n\n{combined_context}"
            else:
                # Sem conhecimento relevante, usar resposta genérica
                response_content = "Não encontrei informações específicas sobre isso na minha base de conhecimento."
            
            processing_time = (datetime.now() - start_time).total_seconds()
        
        # 6. Criar registro de conversa
        conversation = ConversationRecord(
            id=f"conv_{session_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_message=message,
            assistant_response=response_content,
            llm_used=selected_llm.value,
            context_retrieved=[entry.id for entry in relevant_knowledge],
            knowledge_learned=[],  # Será preenchido pelo sistema de evolução
            processing_time=processing_time
        )
        
        # 7. Processar para aprendizado (assíncrono)
        try:
            asyncio.create_task(evolution_engine.process_conversation(conversation, workspace_id))
        except Exception as e:
            logger.error(f"Erro ao processar conversa para aprendizado: {e}")
        
        # 8. Adicionar ao histórico
        try:
            knowledge_manager.add_conversation(workspace_id, conversation)
        except Exception as e:
            logger.error(f"Erro ao adicionar conversa ao histórico: {e}")
        
        return {
            "response": response_content,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "status": "success",
            "metadata": {
                "llm_used": selected_llm.value,
                "context_type": context_type.value,
                "confidence": confidence,
                "knowledge_used": len(relevant_knowledge),
                "file_context_used": bool(file_context),
                "processing_time": processing_time,
                "knowledge_applied": bool(relevant_knowledge) or bool(file_context),
                "workspace_id": workspace_id  # Incluir workspace_id nos metadados
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no chat com conhecimento: {e}")
        # Fallback para processamento tradicional
        return await process_chat_fallback(session_id, message, workspace_id)

async def process_chat_fallback(session_id: str, message: str, workspace_id: str = "default") -> Dict:
    """
    Processamento de chat tradicional como fallback
    """
    try:
        # Tentar usar conhecimento sem LLM
        from app.knowledge import knowledge_manager
        from app.knowledge.file_integration import get_file_context_for_chat
        
        # Log do workspace sendo usado
        logger.info(f"Processando chat fallback para workspace_id: {workspace_id}")
        
        # Buscar conhecimento relevante
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=5)
        
        # Verificar se há referências a arquivos
        file_context = get_file_context_for_chat(workspace_id, message)
        
        # Construir resposta baseada no conhecimento encontrado
        response_parts = []
        
        if relevant_knowledge:
            response_parts.append("Com base no conhecimento disponível:")
            for entry in relevant_knowledge:
                response_parts.append(f"- {entry.content}")
                # Atualizar estatísticas de uso
                knowledge_manager.update_knowledge_usage(workspace_id, entry.id)
        
        if file_context:
            if not response_parts:
                response_parts.append("Encontrei as seguintes informações:")
            response_parts.append(file_context)
        
        if response_parts:
            response_content = "\n\n".join(response_parts)
        else:
            response_content = "Não encontrei informações específicas sobre isso na minha base de conhecimento."
        
        return {
            "response": response_content,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "status": "success",
            "metadata": {
                "llm_used": "fallback",
                "knowledge_used": len(relevant_knowledge),
                "file_context_used": bool(file_context),
                "workspace_id": workspace_id  # Incluir workspace_id nos metadados
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no fallback do chat: {e}")
        return {
            "response": f"Desculpe, ocorreu um erro ao processar sua mensagem: {e}",
            "session_id": session_id,
            "timestamp": datetime.now(),
            "status": "error",
            "metadata": {
                "error": str(e),
                "workspace_id": workspace_id  # Incluir workspace_id nos metadados
            }
        }

