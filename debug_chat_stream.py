#!/usr/bin/env python3
"""
Script para simular e depurar o endpoint de streaming do chat.
"""
import json
import uuid
from typing import Dict, List, Optional, Union, Any, AsyncGenerator

# Simulação das classes necessárias
class Role:
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message:
    def __init__(self, role, content=None, tool_calls=None, name=None, tool_call_id=None, base64_image=None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.name = name
        self.tool_call_id = tool_call_id
        self.base64_image = base64_image
    
    @classmethod
    def user_message(cls, content):
        return cls(role=Role.USER, content=content)
    
    @classmethod
    def system_message(cls, content):
        return cls(role=Role.SYSTEM, content=content)

class Memory:
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        self.messages.append(message)

class ToolCallAgent:
    def __init__(self, name):
        self.name = name
        self.memory = Memory()
        self.system_prompt = "You are a helpful assistant."
        self.messages = []
    
    async def run_with_streaming(self):
        # Simulação do método que causa o erro
        yield {"step": 1, "max_steps": 10}
        
        # Simulação de um chunk de conteúdo
        yield "Hello, how can I help you today?"
        
        # Simulação de um erro
        # Descomente a linha abaixo para simular o erro
        # yield {"error": "Simulated error"}
        
        # Simulação de uma resposta final
        yield {"final": "I'm here to assist you with any questions or tasks."}

# Simulação do endpoint de streaming
async def process_chat_stream(session_id: str, message: str, workspace_id: str = "default"):
    """Process a chat message and stream the response."""
    try:
        # Simulação de obtenção do agente
        agent = ToolCallAgent(name=f"agent_{session_id}")
        
        # Adicionar mensagem do usuário à memória do agente
        user_message = Message(
            role=Role.USER,
            content=message
        )
        agent.memory.add_message(user_message)
        
        # Iniciar streaming
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        
        # Executar agente com streaming
        async for chunk in agent.run_with_streaming():
            if isinstance(chunk, str) and chunk.strip():
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            elif isinstance(chunk, dict):
                yield f"data: {json.dumps({'type': 'status', 'data': chunk})}\n\n"
        
        # Finalizar streaming
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        print(f"Error in streaming chat: {e}")
        error_message = str(e)
        yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"

# Função para testar o processamento de streaming
async def test_process_chat_stream():
    session_id = str(uuid.uuid4())
    message = "Hello, how are you?"
    workspace_id = "test"
    
    print(f"Testing process_chat_stream with session_id={session_id}, workspace_id={workspace_id}")
    
    async for chunk in process_chat_stream(session_id, message, workspace_id):
        print(f"Chunk: {chunk}")

# Função principal
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_process_chat_stream())

