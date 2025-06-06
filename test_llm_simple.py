#!/usr/bin/env python3
"""
Script de teste simplificado para verificar apenas o carregamento de configuração do LLM
"""

import sys
import os
import asyncio

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/ubuntu/projects/ouds/OpenManus')

async def test_llm_config_loading_simple():
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
        
        # Teste 2: Inicializar LLM com config_name="manus" (fallback para default)
        print("\n2. Testando inicialização com config_name='manus' (fallback)...")
        llm_manus = LLM(config_name="manus")
        
        print(f"✅ Modelo carregado: {llm_manus.model}")
        print(f"✅ API Key: {llm_manus.settings.api_key[:10]}...{llm_manus.settings.api_key[-4:]}")
        print(f"✅ Base URL: {llm_manus.settings.base_url}")
        print(f"✅ API Type: {llm_manus.settings.api_type}")
        
        # Teste 3: Testar uma requisição simples
        print("\n3. Testando requisição à API...")
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

async def main():
    """Executa o teste."""
    print("🔧 Testando correção do carregamento de configuração (Simplificado)")
    print("=" * 80)
    
    # Teste: Carregamento direto do LLM
    print("\nTESTE: Carregamento direto do LLM com config_name")
    llm_ok = await test_llm_config_loading_simple()
    
    print("\n" + "=" * 80)
    if llm_ok:
        print("✅ TESTE PASSOU: Configuração carregada corretamente!")
        print("\nO LLM agora carrega a configuração do config.toml corretamente.")
        print("O servidor deve funcionar após reinicialização.")
    else:
        print("❌ TESTE FALHOU: Verifique a implementação")
    
    return llm_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

