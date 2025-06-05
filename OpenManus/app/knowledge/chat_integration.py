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

async def process_chat_with_knowledge(session_id: str, message: str, workspace_id: str = "default") -> Dict:
    """
    Processa chat com integração completa do sistema de conhecimento
    """
    try:
        # Importar módulos de conhecimento
        from app.knowledge import knowledge_manager, llm_router, evolution_engine, ConversationRecord, get_system_context_for_llm, get_file_context_for_chat
        
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
        
        # 3. Classificar contexto e selecionar LLM
        context_type = llm_router.classify_context(message)
        selected_llm, confidence = llm_router.select_llm(context_type, workspace_id)
        
        # 4. Preparar contexto com conhecimento global, do workspace e arquivos
        context_messages = []
        
        # Adicionar conhecimento global do sistema (sempre incluído)
        global_context = get_system_context_for_llm(max_entries=15)
        if global_context:
            context_messages.append({
                "role": "system",
                "content": global_context
            })
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
                response_content = f"Com base no conhecimento disponível: {combined_context}"
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
                "knowledge_applied": bool(relevant_knowledge) or bool(file_context)
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
        from app.knowledge import knowledge_manager, get_file_context_for_chat
        
        # Buscar conhecimento relevante
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=5)
        
        # Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        
        # Construir resposta baseada no conhecimento e arquivos encontrados
        if relevant_knowledge or file_context:
            response = "Com base no conhecimento disponível:\n\n"
            
            # Adicionar conhecimento do workspace
            if relevant_knowledge:
                for entry in relevant_knowledge:
                    response += f"- {entry.content}\n"
                
                if file_context:
                    response += "\n\n"
            
            # Adicionar contexto de arquivos
            if file_context:
                response += f"Informações de arquivos:\n{file_context}"
            
            return {
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now(),
                "status": "success",
                "metadata": {
                    "fallback": True,
                    "knowledge_based": True,
                    "knowledge_count": len(relevant_knowledge),
                    "file_context_used": bool(file_context)
                }
            }
        
        # Se não encontrou conhecimento, tentar usar o agente tradicional
        try:
            from app.session_manager import session_manager
            from app.schema import Message, Role
            
            # Usar o agente tradicional como fallback
            agent = session_manager.agents[workspace_id][session_id]
            
            # Processar mensagem
            user_message = Message(role=Role.USER, content=message)
            agent.memory.add_message(user_message)
            
            await agent.run(message)
            
            # Obter resposta
            assistant_messages = [
                msg for msg in agent.memory.messages 
                if msg.role == Role.ASSISTANT
            ]
            
            response_content = assistant_messages[-1].content if assistant_messages else "Processamento concluído."
            
            return {
                "response": response_content,
                "session_id": session_id,
                "timestamp": datetime.now(),
                "status": "success",
                "metadata": {
                    "llm_used": "traditional_agent",
                    "fallback": True
                }
            }
        except Exception as e:
            logger.error(f"Erro no fallback do agente: {e}")
            
            # Último fallback - resposta genérica
            return {
                "response": "Não encontrei informações específicas sobre isso na minha base de conhecimento.",
                "session_id": session_id,
                "timestamp": datetime.now(),
                "status": "partial",
                "metadata": {
                    "fallback": True,
                    "error": str(e)
                }
            }
        
    except Exception as e:
        logger.error(f"Erro no fallback do chat: {e}")
        return {
            "response": "Desculpe, ocorreu um erro ao processar sua mensagem.",
            "session_id": session_id,
            "timestamp": datetime.now(),
            "status": "error",
            "error": str(e)
        }

# Função para streaming com conhecimento
async def stream_chat_with_knowledge(session_id: str, message: str, workspace_id: str = "default"):
    """
    Streaming de chat com sistema de conhecimento
    """
    try:
        from app.knowledge import knowledge_manager, llm_router, evolution_engine, get_file_context_for_chat
        
        # Buscar conhecimento relevante
        relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=3)
        
        # Verificar se há referências a arquivos na mensagem
        file_context = get_file_context_for_chat(workspace_id, message)
        
        # Classificar contexto e selecionar LLM
        context_type = llm_router.classify_context(message)
        selected_llm, confidence = llm_router.select_llm(context_type, workspace_id)
        
        # Preparar contexto
        context_messages = []
        
        # Adicionar conhecimento do workspace
        if relevant_knowledge:
            knowledge_context = "Conhecimento relevante:\n"
            for entry in relevant_knowledge:
                knowledge_context += f"- {entry.content}\n"
            
            context_messages.append({
                "role": "system",
                "content": knowledge_context
            })
        
        # Adicionar contexto de arquivos
        if file_context:
            context_messages.append({
                "role": "system",
                "content": f"Informações de arquivos:\n{file_context}"
            })
        
        # Adicionar mensagem do usuário
        context_messages.append({
            "role": "user",
            "content": message
        })
        
        # Yield informações iniciais
        yield f"data: {json.dumps({'type': 'metadata', 'llm': selected_llm.value, 'context': context_type.value, 'knowledge_count': len(relevant_knowledge), 'file_context': bool(file_context)})}\n\n"
        
        # Simular streaming (implementação completa dependeria da API específica)
        response_parts = []
        
        try:
            # Para demonstração, vamos simular chunks de resposta
            full_response = await llm_router.call_llm(selected_llm, context_messages, workspace_id)
            
            if selected_llm.value.startswith("openai"):
                response_text = full_response["choices"][0]["message"]["content"]
            elif selected_llm.value.startswith("anthropic"):
                response_text = full_response["content"][0]["text"]
            else:
                response_text = str(full_response)
                
            # Dividir em chunks para simular streaming
            words = response_text.split()
            chunks = [" ".join(words[i:i+5]) for i in range(0, len(words), 5)]
            
            for chunk in chunks:
                response_parts.append(chunk)
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                await asyncio.sleep(0.1)  # Simular delay
                
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            
            # Fallback para conhecimento direto
            if relevant_knowledge or file_context:
                fallback_response = "Com base no conhecimento disponível:\n"
                
                # Adicionar conhecimento do workspace
                if relevant_knowledge:
                    for entry in relevant_knowledge:
                        chunk = f"- {entry.content}\n"
                        fallback_response += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk, 'fallback': True})}\n\n"
                        await asyncio.sleep(0.1)
                
                # Adicionar contexto de arquivos
                if file_context:
                    chunks = file_context.split('\n')
                    for chunk in chunks:
                        chunk_with_newline = chunk + "\n"
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk_with_newline, 'fallback': True})}\n\n"
                        await asyncio.sleep(0.1)
            else:
                fallback_chunk = "Não encontrei informações específicas sobre isso."
                yield f"data: {json.dumps({'type': 'content', 'content': fallback_chunk, 'fallback': True})}\n\n"
        
        # Finalizar streaming
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
        
        # Registrar conversa
        try:
            full_response = " ".join(response_parts)
            conversation = ConversationRecord(
                id=f"conv_{session_id}_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_message=message,
                assistant_response=full_response,
                llm_used=selected_llm.value,
                context_retrieved=[entry.id for entry in relevant_knowledge],
                knowledge_learned=[]
            )
            
            # Processar para aprendizado (assíncrono)
            asyncio.create_task(evolution_engine.process_conversation(conversation, workspace_id))
            
            # Adicionar ao histórico
            knowledge_manager.add_conversation(workspace_id, conversation)
        except Exception as e:
            logger.error(f"Erro ao registrar conversa de streaming: {e}")
            
    except Exception as e:
        logger.error(f"Erro no streaming de chat: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

