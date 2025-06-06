#!/usr/bin/env python3
"""
Script de debug para verificar o carregamento da configuração
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

def debug_config_loading():
    """Debug do carregamento da configuração."""
    try:
        print("🔧 Debug do carregamento da configuração...")
        print("=" * 60)
        
        # Teste 1: Verificar se o arquivo config.toml existe e pode ser lido
        print("1. Verificando arquivo config.toml...")
        from pathlib import Path
        config_path = Path('/home/ubuntu/projects/ouds/OpenManus/config/config.toml')
        
        if config_path.exists():
            print(f"✅ Arquivo existe: {config_path}")
            with open(config_path, 'r') as f:
                content = f.read()
                print(f"✅ Tamanho do arquivo: {len(content)} bytes")
                # Verificar se contém a chave de API
                if 'sk-proj-' in content:
                    print("✅ Chave de API encontrada no arquivo")
                else:
                    print("❌ Chave de API NÃO encontrada no arquivo")
        else:
            print(f"❌ Arquivo NÃO existe: {config_path}")
            return False
        
        # Teste 2: Verificar carregamento da configuração
        print("\n2. Verificando carregamento da configuração...")
        from app.config import config
        
        print(f"✅ Config carregado: {type(config)}")
        print(f"✅ LLM configs disponíveis: {list(config.llm.keys())}")
        
        # Teste 3: Verificar configuração default
        print("\n3. Verificando configuração default...")
        default_config = config.llm.get("default")
        if default_config:
            print(f"✅ Configuração default encontrada")
            print(f"  - Modelo: {default_config.model}")
            print(f"  - Base URL: {default_config.base_url}")
            print(f"  - API Key: {default_config.api_key[:10]}...{default_config.api_key[-4:]}")
            print(f"  - API Type: {default_config.api_type}")
            
            if default_config.api_key == "default_key":
                print("❌ PROBLEMA: Ainda usando 'default_key'!")
                return False
            else:
                print("✅ Chave de API carregada corretamente")
        else:
            print("❌ Configuração default NÃO encontrada")
            return False
        
        # Teste 4: Testar inicialização do LLM
        print("\n4. Testando inicialização do LLM...")
        from app.llm import LLM
        
        llm = LLM(config_name="default")
        print(f"✅ LLM inicializado")
        print(f"  - Modelo: {llm.model}")
        print(f"  - API Key: {llm.settings.api_key[:10]}...{llm.settings.api_key[-4:]}")
        
        if llm.settings.api_key == "default_key":
            print("❌ PROBLEMA: LLM ainda usando 'default_key'!")
            return False
        else:
            print("✅ LLM usando chave correta")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_raw_toml_loading():
    """Debug do carregamento direto do TOML."""
    try:
        print("\n🔧 Debug do carregamento direto do TOML...")
        print("=" * 60)
        
        import tomllib
        from pathlib import Path
        
        config_path = Path('/home/ubuntu/projects/ouds/OpenManus/config/config.toml')
        
        with config_path.open("rb") as f:
            raw_config = tomllib.load(f)
        
        print("✅ TOML carregado diretamente")
        print(f"Chaves principais: {list(raw_config.keys())}")
        
        if 'llm' in raw_config:
            llm_config = raw_config['llm']
            print(f"Configuração LLM: {llm_config}")
            
            if 'api_key' in llm_config:
                api_key = llm_config['api_key']
                print(f"API Key no TOML: {api_key[:10]}...{api_key[-4:]}")
                
                if api_key.startswith('sk-proj-'):
                    print("✅ Chave de API válida encontrada no TOML")
                    return True
                else:
                    print("❌ Chave de API inválida no TOML")
                    return False
            else:
                print("❌ api_key não encontrada na configuração LLM")
                return False
        else:
            print("❌ Seção [llm] não encontrada no TOML")
            return False
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante debug do TOML: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os debugs."""
    print("🔧 Debug completo do carregamento de configuração")
    print("=" * 80)
    
    # Debug 1: Carregamento direto do TOML
    toml_ok = debug_raw_toml_loading()
    
    # Debug 2: Carregamento da configuração
    config_ok = debug_config_loading()
    
    print("\n" + "=" * 80)
    if toml_ok and config_ok:
        print("✅ TODOS OS DEBUGS PASSARAM: Configuração funcionando!")
    else:
        print("❌ PROBLEMAS ENCONTRADOS:")
        if not toml_ok:
            print("  - Problema no carregamento direto do TOML")
        if not config_ok:
            print("  - Problema no carregamento da configuração")
    
    return toml_ok and config_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

