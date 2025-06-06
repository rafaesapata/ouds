#!/usr/bin/env python3
"""
Script para verificar onde o servidor está procurando o config.toml
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

def check_project_root():
    """Verifica onde o PROJECT_ROOT está apontando."""
    try:
        from app.config import PROJECT_ROOT, get_project_root
        
        print("🔧 Verificando PROJECT_ROOT...")
        print("=" * 60)
        
        print(f"PROJECT_ROOT atual: {PROJECT_ROOT}")
        print(f"get_project_root(): {get_project_root()}")
        
        # Verificar se o config.toml existe no PROJECT_ROOT
        config_path = PROJECT_ROOT / "config" / "config.toml"
        print(f"Caminho esperado do config: {config_path}")
        print(f"Arquivo existe: {config_path.exists()}")
        
        if config_path.exists():
            print("✅ Config encontrado no PROJECT_ROOT")
        else:
            print("❌ Config NÃO encontrado no PROJECT_ROOT")
            
            # Verificar onde o arquivo realmente está
            possible_paths = [
                "/home/ubuntu/projects/ouds/OpenManus/config/config.toml",
                "/opt/.manus/.versions/20250601161335/config/config.toml",
                "/opt/.manus/.versions/20250601161335/config.toml"
            ]
            
            print("\nVerificando caminhos possíveis:")
            for path in possible_paths:
                exists = Path(path).exists()
                print(f"  {path}: {'✅' if exists else '❌'}")
        
        return config_path.exists()
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_server_environment():
    """Verifica o ambiente do servidor."""
    try:
        print("\n🔧 Verificando ambiente do servidor...")
        print("=" * 60)
        
        print(f"Diretório atual: {os.getcwd()}")
        print(f"__file__ seria: {Path(__file__).resolve()}")
        
        # Simular o que acontece no servidor
        server_file = Path("/opt/.manus/.versions/20250601161335/app/config.py")
        if server_file.exists():
            server_root = server_file.parent.parent
            print(f"PROJECT_ROOT do servidor seria: {server_root}")
            
            server_config_path = server_root / "config" / "config.toml"
            print(f"Caminho do config no servidor: {server_config_path}")
            print(f"Existe: {server_config_path.exists()}")
        else:
            print("❌ Arquivo config.py do servidor não encontrado")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Executa todas as verificações."""
    print("🔧 Verificação de caminhos de configuração")
    print("=" * 80)
    
    check_project_root()
    check_server_environment()
    
    print("\n" + "=" * 80)
    print("Conclusão: O servidor pode estar procurando o config em um local diferente")

if __name__ == "__main__":
    main()

