#!/usr/bin/env python3
"""
Script para testar se a classe Config tem os atributos openai_api_key, openai_api_base e openai_organization.
"""

import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # Importar a classe Config
    from OpenManus.app.config import config
    
    # Verificar se a classe Config tem os atributos openai_api_key, openai_api_base e openai_organization
    attributes = ["openai_api_key", "openai_api_base", "openai_organization"]
    missing_attributes = []
    
    for attr in attributes:
        try:
            value = getattr(config, attr)
            print(f"✅ Atributo {attr} existe: {value}")
        except AttributeError:
            missing_attributes.append(attr)
            print(f"❌ Atributo {attr} não existe")
    
    if missing_attributes:
        print(f"\n❌ TESTE FALHOU: Os seguintes atributos estão faltando: {', '.join(missing_attributes)}")
        sys.exit(1)
    else:
        print("\n✅ TESTE PASSOU: Todos os atributos existem na classe Config")
        sys.exit(0)
    
except Exception as e:
    print(f"❌ Erro ao testar a classe Config: {e}")
    sys.exit(1)

