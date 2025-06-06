#!/usr/bin/env python3
"""
Script de teste para verificar se o LLM carrega a configuração corretamente com config_name
"""

import sys
import os
import asyncio

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

async def test_llm_config_loading():
    """Testa se o LLM carrega a configuração corretamente."""
    try:
        from app.llm import LLM
        
        print("🔧 Testando carregamento de configuração pelo LLM...")
        print("=" * 60)
        
        # Teste 1: Inicializar LLM com config_name="default"
        print("1. Testando inicialização com config_name='default'...")
        llm_default = LLM(config_name="default")
        
        print(f"✅ Modelo carregado: {llm_default.model}")
        print(f"✅ API Key: {llm_default.settings.api_key[:10]}...{llm_default.settings.api_key[-4:]}")
        print(f"✅ Base URL: {llm_default.settings.base_url}")
        print(f"✅ API Type: {llm_default.settings.api_type}")
        
        # Teste 2: Testar uma requisição simples
        print("\n2. Testando requisição à API...")
        from app.schema import Message
        
        test_messages = [
            Message.user_message("Responda apenas 'CONFIGURAÇÃO OK' se você conseguir me ouvir.")
        ]
        
        response = await llm_default.ask(test_messages)
        
        if response and hasattr(response, 'content'):
            print("✅ TESTE PASSOU: LLM carregou configuração corretamente!")
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

async def test_agent_initialization():
    """Testa se o agente inicializa corretamente com a nova configuração."""
    try:
        from app.agent.base import BaseAgent
        from app.agent.manus import ManusAgent
        
        print("\n🔧 Testando inicialização do agente...")
        print("=" * 60)
        
        # Criar uma instância do agente Manus
        agent = ManusAgent()
        
        print(f"✅ Agente criado: {agent.name}")
        print(f"✅ LLM inicializado: {type(agent.llm).__name__}")
        print(f"✅ Modelo do LLM: {agent.llm.model}")
        print(f"✅ API Key: {agent.llm.settings.api_key[:10]}...{agent.llm.settings.api_key[-4:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: Exceção durante teste do agente: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Executa todos os testes."""
    print("🔧 Testando correção do carregamento de configuração")
    print("=" * 80)
    
    # Teste 1: Carregamento direto do LLM
    print("\nTESTE 1: Carregamento direto do LLM com config_name")
    llm_ok = await test_llm_config_loading()
    
    # Teste 2: Inicialização do agente
    print("\nTESTE 2: Inicialização do agente")
    agent_ok = await test_agent_initialization()
    
    print("\n" + "=" * 80)
    if llm_ok and agent_ok:
        print("✅ TODOS OS TESTES PASSARAM: Configuração carregada corretamente!")
        print("\nO servidor agora deve funcionar corretamente com a configuração OpenAI.")
    else:
        print("❌ ALGUNS TESTES FALHARAM: Verifique a implementação")
    
    return llm_ok and agent_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

