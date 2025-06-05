"""
Módulo simplificado para streaming de chat.
Este módulo implementa uma versão extremamente simplificada do streaming de chat
que não depende de objetos complexos ou métodos que possam causar erros.
"""
import json
import logging
import os
from typing import AsyncGenerator, Dict, List, Optional, Any

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do LLM
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000

# Importações necessárias
try:
    import aiohttp
except ImportError:
    logger.warning("aiohttp não disponível - funcionalidades de HTTP assíncrono limitadas")

try:
    from openai import AsyncOpenAI
except ImportError:
    logger.error("Falha ao importar OpenAI - instale com: pip install openai")

# Importar configurações
try:
    # Tentar importar configurações simplificadas
    from app.chat_stream_config import API_KEY, API_BASE, MODEL, TEMPERATURE, MAX_TOKENS
    logger.info("Usando configurações simplificadas para streaming de chat")
except ImportError:
    logger.warning("Falha ao importar configurações simplificadas - usando variáveis de ambiente")
    # Configuração de fallback
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    MODEL = DEFAULT_MODEL
    TEMPERATURE = DEFAULT_TEMPERATURE
    MAX_TOKENS = DEFAULT_MAX_TOKENS

# Importar função de contexto de conhecimento
try:
    # Importar diretamente do módulo chat_integration
    from app.knowledge.chat_integration import get_context_for_chat
    logger.info("Função get_context_for_chat importada com sucesso")
except ImportError:
    logger.error("Falha ao importar get_context_for_chat - contexto de conhecimento não estará disponível")
    
    # Função de fallback simplificada
    async def get_context_for_chat(message, workspace_id):
        """Função de fallback para get_context_for_chat"""
        logger.warning(f"Usando função de fallback para get_context_for_chat (workspace: {workspace_id})")
        try:
            # Tentar importar o módulo knowledge_manager diretamente
            from app.knowledge import knowledge_manager
            
            # Buscar conhecimento relevante do workspace
            relevant_knowledge = knowledge_manager.search_knowledge(workspace_id, message, limit=3)
            
            if relevant_knowledge:
                context = "Conhecimento relevante:\n"
                for entry in relevant_knowledge:
                    context += f"- {entry.content}\n"
                return context
        except Exception as e:
            logger.error(f"Erro na função de fallback para get_context_for_chat: {e}")
        
        return None


async def simple_chat_stream_endpoint(request: Request):
    """
    Endpoint simplificado para streaming de chat que não depende de objetos complexos.
    """
    try:
        # Parse request body
        body = await request.json()
        message = body.get("message", "")
        session_id = body.get("session_id", "")
        workspace_id = body.get("workspace_id", "default")
        
        # Log request
        logger.info(f"Streaming chat request: session={session_id}, workspace={workspace_id}, message={message[:50]}...")
        
        # Create streaming response
        return StreamingResponse(
            direct_chat_stream(message, session_id, workspace_id),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def direct_chat_stream(message: str, session_id: str, workspace_id: str = "default") -> AsyncGenerator[str, None]:
    """
    Implementação direta de streaming de chat sem dependências complexas.
    """
    try:
        # Start streaming
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        
        # Get context from knowledge system if available
        context = ""
        try:
            context_result = await get_context_for_chat(message, workspace_id)
            if context_result:
                context = f"Context from knowledge base: {context_result}"
                logger.info(f"Applied context to message: {len(context_result)} chars")
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            # Continue without context
        
        # Create OpenAI client directly
        try:
            client = AsyncOpenAI(
                api_key=API_KEY,
                base_url=API_BASE,
            )
            
            # Prepare messages
            messages = []
            
            # Add system message
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant. Respond to the user's message."
            })
            
            # Add user message with context if available
            user_content = message
            if context:
                user_content += f"\n\nRelevant context: {context}"
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Stream response directly from OpenAI
            try:
                # Make the API call with streaming
                stream = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=True
                )
                
                # Process streaming response
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
            except Exception as e:
                logger.error(f"Error in OpenAI streaming: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                # Fallback response
                yield f"data: {json.dumps({'type': 'chunk', 'content': 'Desculpe, ocorreu um erro ao processar sua mensagem.'})}\n\n"
        except Exception as e:
            logger.error(f"Error creating OpenAI client: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            # Fallback response
            yield f"data: {json.dumps({'type': 'chunk', 'content': 'Desculpe, ocorreu um erro ao conectar com o serviço de IA.'})}\n\n"
        
        # End streaming
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in direct chat stream: {e}", exc_info=True)
        error_message = str(e)
        yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
        # Fallback response
        yield f"data: {json.dumps({'type': 'chunk', 'content': 'Desculpe, ocorreu um erro inesperado.'})}\n\n"
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"