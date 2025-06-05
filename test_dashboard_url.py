import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_url():
    """Testar busca específica por URL do dashboard APN"""
    from OpenManus.app.knowledge.file_integration import file_access_manager, get_file_context_for_chat
    
    # Workspace específico para teste
    workspace_id = "test_workspace"
    
    # Testar contexto de arquivos com menção ao dashboard APN
    messages = [
        "Qual é a URL do dashboard APN?",
        "Onde encontro o dashboard da APN?",
        "Me informe o site do dashboard APN",
        "Preciso acessar o dashboard APN"
    ]
    
    for message in messages:
        file_context = get_file_context_for_chat(workspace_id, message)
        print(f"\nContexto para '{message}':")
        print(file_context if file_context else "Nenhum contexto encontrado")

if __name__ == "__main__":
    test_dashboard_url()

