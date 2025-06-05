"""
Módulo simplificado para streaming de chat.
Este módulo implementa uma versão extremamente simplificada do streaming de chat
que não depende de objetos complexos ou métodos que possam causar erros.
"""
import json
import logging
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
    from openai import AsyncOpenAI
    from app.knowledge.chat_integration import get_context_for_chat
except ImportError:
    logger.error("Falha ao importar dependências necessárias")


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
        from app.config import config
        client = AsyncOpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.api_base,
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
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
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
        
        # End streaming
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in direct chat stream: {e}", exc_info=True)
        error_message = str(e)
        yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"

