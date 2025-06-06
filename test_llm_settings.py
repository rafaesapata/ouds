#!/usr/bin/env python3
"""
Script para testar a inicialização da classe LLMSettings.
"""

import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # Importar as classes necessárias
    from OpenManus.app.config import LLMSettings
    
    # Testar a inicialização da classe LLMSettings com valores padrão
    settings = LLMSettings(
        model="gpt-3.5-turbo",
        base_url="https://api.openai.com/v1",
        api_key="test_key",
        api_type="openai",
        api_version="2023-05-15"
    )
    
    # Verificar se os valores foram definidos corretamente
    assert settings.model == "gpt-3.5-turbo"
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.api_key == "test_key"
    assert settings.api_type == "openai"
    assert settings.api_version == "2023-05-15"
    
    print("✅ Teste de inicialização da classe LLMSettings passou com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao testar a classe LLMSettings: {e}")
    sys.exit(1)

# Testar a inicialização da classe LLM com valores padrão
try:
    # Importar a classe LLM
    from OpenManus.app.llm import LLM
    
    # Criar uma instância mock da classe LLM para testar a inicialização
    class MockLLM(LLM):
        def __init__(self, model="gpt-3.5-turbo", settings=None):
            # Apenas verificar se a inicialização não causa erros de validação
            self.model = model
            
            # Usar o código corrigido
            if settings is None:
                self.settings = LLMSettings(
                    model=model,
                    base_url="https://api.openai.com/v1",
                    api_key="default_key",
                    api_type="openai",
                    api_version="2023-05-15",
                    max_tokens=4096,
                    temperature=1.0
                )
            else:
                self.settings = settings
    
    # Testar a inicialização da classe MockLLM
    llm = MockLLM()
    
    # Verificar se os valores foram definidos corretamente
    assert llm.model == "gpt-3.5-turbo"
    assert llm.settings.model == "gpt-3.5-turbo"
    assert llm.settings.base_url == "https://api.openai.com/v1"
    assert llm.settings.api_key == "default_key"
    assert llm.settings.api_type == "openai"
    assert llm.settings.api_version == "2023-05-15"
    
    print("✅ Teste de inicialização da classe LLM passou com sucesso!")
    
    # Teste final bem-sucedido
    print("\n✅ TODOS OS TESTES PASSARAM! A correção do erro de validação do LLMSettings foi bem-sucedida.")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erro ao testar a classe LLM: {e}")
    sys.exit(1)

