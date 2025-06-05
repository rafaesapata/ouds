import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_chat_integration():
    """Testar integração do chat com conhecimento e arquivos em um workspace específico"""
    from OpenManus.app.knowledge.chat_integration import process_chat_with_knowledge
    
    # Workspace específico para teste
    workspace_id = "test_workspace"
    session_id = "test_session"
    
    # Testar chat com menção explícita a arquivo
    message = "Leia o arquivo test_dashboard.txt"
    result = await process_chat_with_knowledge(session_id, message, workspace_id)
    print(f"\nResposta para '{message}':")
    print(result["response"])
    
    # Testar chat com pergunta sobre conteúdo do arquivo
    message = "Qual é a URL do dashboard APN?"
    result = await process_chat_with_knowledge(session_id, message, workspace_id)
    print(f"\nResposta para '{message}':")
    print(result["response"])
    
    # Testar chat com pergunta sobre arquivos disponíveis
    message = "Quais arquivos estão disponíveis?"
    result = await process_chat_with_knowledge(session_id, message, workspace_id)
    print(f"\nResposta para '{message}':")
    print(result["response"])

if __name__ == "__main__":
    asyncio.run(test_chat_integration())

