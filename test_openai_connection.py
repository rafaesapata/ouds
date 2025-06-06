#!/usr/bin/env python3
"""
Script de teste para verificar a conectividade com a API OpenAI
"""

import sys
import os
import asyncio

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

async def test_openai_connection():
    """Testa a conectividade com a API OpenAI."""
    try:
        from app.config import config
        from app.llm import LLM
        
        print("🔧 Testando conectividade com a API OpenAI...")
        print("=" * 60)
        
        # Verificar se a configuração foi carregada
        print("1. Verificando configuração...")
        llm_config = config.llm.get("default")
        if not llm_config:
            print("❌ ERRO: Configuração LLM não encontrada")
            return False
        
        print(f"✅ Modelo: {llm_config.model}")
        print(f"✅ Base URL: {llm_config.base_url}")
        print(f"✅ API Type: {llm_config.api_type}")
        
        # Verificar se a chave da API está configurada
        if not llm_config.api_key or llm_config.api_key == "YOUR_OPENAI_API_KEY":
            print("❌ ERRO: Chave da API não configurada")
            return False
        
        print(f"✅ API Key: {llm_config.api_key[:10]}...{llm_config.api_key[-4:]}")
        
        # Inicializar o LLM
        print("\n2. Inicializando LLM...")
        llm = LLM(
            model=llm_config.model,
            settings=llm_config,
            api_key=llm_config.api_key,
            api_base=llm_config.base_url,
            api_version=llm_config.api_version
        )
        print("✅ LLM inicializado com sucesso")
        
        # Testar uma requisição simples
        print("\n3. Testando requisição à API...")
        from app.schema import Message
        
        test_messages = [
            Message.user_message("Olá! Este é um teste de conectividade. Responda apenas 'OK'.")
        ]
        
        response = await llm.ask(test_messages)
        
        if response and hasattr(response, 'content'):
            print("✅ TESTE PASSOU: Conectividade com a API OpenAI funcionando!")
            print(f"Resposta da API: {response.content}")
            return True
        else:
            print("❌ TESTE FALHOU: Resposta inválida da API")
            return False
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_loading():
    """Testa se a configuração está sendo carregada corretamente."""
    try:
        from app.config import config
        
        print("🔧 Testando carregamento da configuração...")
        print("=" * 60)
        
        # Verificar se o arquivo config.toml existe
        config_path = config.root_path / "config" / "config.toml"
        if not config_path.exists():
            print("❌ ERRO: Arquivo config.toml não encontrado")
            return False
        
        print("✅ Arquivo config.toml encontrado")
        
        # Verificar se a configuração LLM foi carregada
        llm_configs = config.llm
        if not llm_configs:
            print("❌ ERRO: Configurações LLM não carregadas")
            return False
        
        print(f"✅ Configurações LLM carregadas: {list(llm_configs.keys())}")
        
        # Verificar configuração padrão
        default_config = llm_configs.get("default")
        if not default_config:
            print("❌ ERRO: Configuração padrão não encontrada")
            return False
        
        print("✅ Configuração padrão carregada")
        print(f"  - Modelo: {default_config.model}")
        print(f"  - Base URL: {default_config.base_url}")
        print(f"  - API Type: {default_config.api_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante teste de configuração: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Executa todos os testes."""
    print("🔧 Testando correção do erro de conexão OpenAI")
    print("=" * 80)
    
    # Teste 1: Carregamento da configuração
    print("\nTESTE 1: Carregamento da configuração")
    config_ok = await test_config_loading()
    
    if not config_ok:
        print("\n❌ TESTE FALHOU: Problema no carregamento da configuração")
        return False
    
    # Teste 2: Conectividade com a API
    print("\nTESTE 2: Conectividade com a API OpenAI")
    connection_ok = await test_openai_connection()
    
    print("\n" + "=" * 80)
    if config_ok and connection_ok:
        print("✅ TODOS OS TESTES PASSARAM: Conectividade com OpenAI restaurada!")
        print("\nO sistema agora deve funcionar corretamente com a API OpenAI.")
    else:
        print("❌ ALGUNS TESTES FALHARAM: Verifique a configuração")
    
    return config_ok and connection_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

