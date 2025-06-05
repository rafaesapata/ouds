import asyncio
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from OpenManus.app.knowledge.workspace_knowledge import knowledge_manager
from OpenManus.app.knowledge.file_integration import get_file_context_for_chat

def test_knowledge():
    # Testar busca de conhecimento
    results = knowledge_manager.search_knowledge('default', 'site do dashboard APN', limit=5)
    print(f'Resultados da busca: {len(results)}')
    for r in results:
        print(f'- {r.content}')
    
    # Testar contexto de arquivos
    file_context = get_file_context_for_chat('default', 'Leia o arquivo test.txt')
    print(f'Contexto de arquivos: {file_context}')
    
    # Construir resposta manual
    if results:
        response = "Com base no conhecimento disponível:\n\n"
        for entry in results:
            response += f"- {entry.content}\n"
        print(f'\nResposta simulada:\n{response}')

if __name__ == "__main__":
    test_knowledge()

