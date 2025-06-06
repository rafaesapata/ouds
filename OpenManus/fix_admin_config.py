"""
OUDS - Admin Config Fix
======================

Script para corrigir a configuração de admin_workspace.
"""

import os
import sys
import json
from datetime import datetime

# Adicionar diretório atual ao path
sys.path.append('.')

# Importar depois de adicionar ao path
from app.settings import settings
from app.admin_schema import SystemVariables, LLMConfiguration, LLMType, LLMProvider, LLMStatus
from app.logger import logger

def fix_admin_config():
    """Corrige a configuração de admin_workspace."""
    config_file = "admin_config.json"
    
    # Verificar se o arquivo existe
    if os.path.exists(config_file):
        # Carregar configuração existente
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Atualizar admin_workspace
        if 'system_variables' in data:
            data['system_variables']['admin_workspace'] = 'rafaelsapata'
            
            # Salvar configuração atualizada
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"Configuração atualizada: admin_workspace = rafaelsapata")
        else:
            print("Seção system_variables não encontrada no arquivo de configuração")
    else:
        print(f"Arquivo {config_file} não encontrado")
        
        # Criar novo arquivo de configuração
        now = datetime.now().isoformat()
        
        # Configuração LLM Text padrão
        text_llm = LLMConfiguration(
            id="default_text",
            llm_type=LLMType.TEXT,
            provider=LLMProvider.OPENAI,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key="API_KEY_PLACEHOLDER",  # Placeholder para não expor chaves
            api_type=settings.llm_api_type,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            status=LLMStatus.ACTIVE if settings.llm_api_key else LLMStatus.INACTIVE,
            is_default=True,
            last_test=now,
            created_at=now,
            updated_at=now
        )
        
        # Configuração LLM Vision padrão
        vision_llm = LLMConfiguration(
            id="default_vision",
            llm_type=LLMType.VISION,
            provider=LLMProvider.OPENAI,
            model=settings.llm_vision_model,
            base_url=settings.llm_vision_base_url,
            api_key="API_KEY_PLACEHOLDER",  # Placeholder para não expor chaves
            api_type=settings.llm_vision_api_type,
            max_tokens=settings.llm_vision_max_tokens,
            temperature=settings.llm_vision_temperature,
            status=LLMStatus.ACTIVE if settings.llm_vision_api_key else LLMStatus.INACTIVE,
            is_default=True,
            last_test=now,
            created_at=now,
            updated_at=now
        )
        
        # Variáveis do sistema
        system_vars = SystemVariables(
            admin_workspace='rafaelsapata',  # Forçar valor correto
            llm_text=text_llm,
            llm_vision=vision_llm,
            environment="development",
            debug_mode=settings.debug
        )
        
        # Salvar configurações
        data = {
            'llm_configurations': [text_llm.model_dump(), vision_llm.model_dump()],
            'system_variables': system_vars.model_dump(),
            'last_updated': now
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Novo arquivo de configuração criado com admin_workspace = rafaelsapata")

if __name__ == "__main__":
    fix_admin_config()

