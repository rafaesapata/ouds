import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_file_integration():
    """Testar integração de arquivos com o sistema de conhecimento"""
    from OpenManus.app.knowledge.file_integration import file_access_manager, get_file_context_for_chat
    
    # Testar com diferentes workspaces
    workspaces = ["default", "test_workspace"]
    
    for workspace_id in workspaces:
        print(f"\n=== Testando workspace: {workspace_id} ===")
        
        # Listar arquivos no workspace
        files = file_access_manager.list_files(workspace_id)
        print(f"Arquivos no workspace: {len(files)}")
        for file in files:
            print(f"- {file['name']} ({file['size']} bytes)")
        
        # Testar contexto de arquivos com diferentes mensagens
        test_messages = [
            "Leia o arquivo test_dashboard.txt",
            "Qual é a URL do dashboard APN?",
            "Quais arquivos estão disponíveis?",
            "Mostre o conteúdo do arquivo",
            "Abra o arquivo test_info.txt"
        ]
        
        for message in test_messages:
            file_context = get_file_context_for_chat(workspace_id, message)
            print(f"\nContexto para '{message}':")
            print(file_context if file_context else "Nenhum contexto encontrado")

if __name__ == "__main__":
    test_file_integration()

