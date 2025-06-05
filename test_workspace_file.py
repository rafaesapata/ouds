import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_file_access():
    """Testar acesso a arquivos em um workspace específico"""
    from OpenManus.app.knowledge.file_integration import file_access_manager, get_file_context_for_chat
    
    # Workspace específico para teste
    workspace_id = "test_workspace"
    
    # Listar arquivos no workspace
    files = file_access_manager.list_files(workspace_id)
    print(f"Arquivos no workspace {workspace_id}: {len(files)}")
    for file in files:
        print(f"- {file['name']} ({file['size']} bytes)")
    
    # Testar contexto de arquivos com menção explícita
    message = "Leia o arquivo test_dashboard.txt"
    file_context = get_file_context_for_chat(workspace_id, message)
    print(f"\nContexto para '{message}':")
    print(file_context)
    
    # Testar contexto de arquivos com menção ao conteúdo
    message = "Qual é a URL do dashboard APN?"
    file_context = get_file_context_for_chat(workspace_id, message)
    print(f"\nContexto para '{message}':")
    print(file_context)
    
    # Testar contexto de arquivos com menção genérica
    message = "Quais arquivos estão disponíveis?"
    file_context = get_file_context_for_chat(workspace_id, message)
    print(f"\nContexto para '{message}':")
    print(file_context)

if __name__ == "__main__":
    test_file_access()

