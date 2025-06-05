import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Criar um arquivo de teste
def create_test_file():
    test_content = """Este é um arquivo de teste para o sistema de conhecimento.
    
Ele contém informações importantes sobre o projeto:
- Nome: OUDS
- Versão: 2.9.1
- Descrição: Sistema de conhecimento para assistentes virtuais
    """
    
    # Obter o caminho do workspace
    from OpenManus.app.config import config
    workspace_path = config.workspace_root / "default" / "files"
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Criar o arquivo
    test_file = workspace_path / "test_info.txt"
    with open(test_file, "w") as f:
        f.write(test_content)
    
    print(f"Arquivo criado: {test_file}")
    return test_file

# Testar acesso ao arquivo
def test_file_access():
    from OpenManus.app.knowledge.file_integration import file_access_manager, get_file_context_for_chat
    
    # Listar arquivos
    files = file_access_manager.list_files("default")
    print(f"Arquivos no workspace: {len(files)}")
    for file in files:
        print(f"- {file['name']} ({file['size']} bytes)")
    
    # Testar contexto de arquivos
    file_context = get_file_context_for_chat("default", "Leia o arquivo test_info.txt")
    print(f"\nContexto de arquivos para 'test_info.txt':")
    print(file_context)
    
    # Testar menção genérica a arquivos
    file_context = get_file_context_for_chat("default", "Quais arquivos estão disponíveis?")
    print(f"\nContexto para pergunta sobre arquivos disponíveis:")
    print(file_context)

if __name__ == "__main__":
    create_test_file()
    test_file_access()

