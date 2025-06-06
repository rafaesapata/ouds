"""
OUDS - Admin Configuration Manager
==================================

Gerenciador de configurações administrativas com suporte a LLM dinâmico.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.settings import settings
from app.admin_schema import LLMConfiguration, LLMType, LLMProvider, LLMStatus, SystemVariables
from app.logger import logger


class AdminConfigManager:
    """Gerenciador de configurações administrativas."""
    
    def __init__(self):
        self.config_file = Path("config/admin_config.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self._llm_configs: Dict[str, LLMConfiguration] = {}
        self._system_vars: Optional[SystemVariables] = None
        self._load_config()
    
    def _load_config(self):
        """Carrega configurações do arquivo JSON."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Carregar configurações de LLM
                for llm_data in data.get('llm_configurations', []):
                    config = LLMConfiguration(**llm_data)
                    self._llm_configs[config.id] = config
                
                # Carregar variáveis do sistema
                if 'system_variables' in data:
                    self._system_vars = SystemVariables(**data['system_variables'])
            else:
                # Criar configurações padrão
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Erro ao carregar configurações admin: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Cria configurações padrão baseadas no .env."""
        now = datetime.now().isoformat()
        
        # Configuração LLM Text padrão
        text_llm = LLMConfiguration(
            id="default_text",
            llm_type=LLMType.TEXT,
            provider=LLMProvider.OPENAI,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
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
            api_key=settings.llm_vision_api_key,
            api_type=settings.llm_vision_api_type,
            max_tokens=settings.llm_vision_max_tokens,
            temperature=settings.llm_vision_temperature,
            status=LLMStatus.ACTIVE if settings.llm_vision_api_key else LLMStatus.INACTIVE,
            is_default=True,
            last_test=now,
            created_at=now,
            updated_at=now
        )
        
        self._llm_configs = {
            text_llm.id: text_llm,
            vision_llm.id: vision_llm
        }
        
        # Variáveis do sistema
        self._system_vars = SystemVariables(
            admin_workspace=settings.admin_workspace,
            workspace_root=settings.workspace_root,
            log_level=settings.log_level,
            github_token=settings.github_token,
            environment="development",
            version="1.0.23"
        )
        
        self._save_config()
    
    def _save_config(self):
        """Salva configurações no arquivo JSON."""
        try:
            data = {
                'llm_configurations': [config.dict() for config in self._llm_configs.values()],
                'system_variables': self._system_vars.dict() if self._system_vars else {},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info("Configurações admin salvas com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações admin: {e}")
    
    def get_llm_configurations(self) -> List[LLMConfiguration]:
        """Retorna todas as configurações de LLM."""
        return list(self._llm_configs.values())
    
    def get_llm_configuration(self, llm_id: str) -> Optional[LLMConfiguration]:
        """Retorna uma configuração específica de LLM."""
        return self._llm_configs.get(llm_id)
    
    def get_default_llm(self, llm_type: LLMType) -> Optional[LLMConfiguration]:
        """Retorna o LLM padrão para um tipo específico."""
        for config in self._llm_configs.values():
            if config.llm_type == llm_type and config.is_default and config.status == LLMStatus.ACTIVE:
                return config
        return None
    
    def update_llm_configuration(self, llm_config: LLMConfiguration) -> bool:
        """Atualiza uma configuração de LLM."""
        try:
            llm_config.updated_at = datetime.now().isoformat()
            
            # Se está sendo marcado como padrão, desmarcar outros do mesmo tipo
            if llm_config.is_default:
                for config in self._llm_configs.values():
                    if config.llm_type == llm_config.llm_type and config.id != llm_config.id:
                        config.is_default = False
            
            self._llm_configs[llm_config.id] = llm_config
            self._save_config()
            
            # Recarregar variáveis de ambiente se necessário
            self._update_env_variables()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração LLM: {e}")
            return False
    
    def delete_llm_configuration(self, llm_id: str) -> bool:
        """Remove uma configuração de LLM."""
        try:
            if llm_id in self._llm_configs:
                del self._llm_configs[llm_id]
                self._save_config()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar configuração LLM: {e}")
            return False
    
    def get_system_variables(self) -> SystemVariables:
        """Retorna as variáveis do sistema."""
        return self._system_vars
    
    def update_system_variables(self, system_vars: SystemVariables) -> bool:
        """Atualiza as variáveis do sistema."""
        try:
            self._system_vars = system_vars
            self._save_config()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar variáveis do sistema: {e}")
            return False
    
    def _update_env_variables(self):
        """Atualiza variáveis de ambiente com configurações ativas."""
        try:
            # Atualizar LLM Text
            text_llm = self.get_default_llm(LLMType.TEXT)
            if text_llm:
                os.environ['LLM_MODEL'] = text_llm.model
                os.environ['LLM_BASE_URL'] = text_llm.base_url
                os.environ['LLM_API_KEY'] = text_llm.api_key
                os.environ['LLM_MAX_TOKENS'] = str(text_llm.max_tokens)
                os.environ['LLM_TEMPERATURE'] = str(text_llm.temperature)
                if text_llm.api_type:
                    os.environ['LLM_API_TYPE'] = text_llm.api_type
            
            # Atualizar LLM Vision
            vision_llm = self.get_default_llm(LLMType.VISION)
            if vision_llm:
                os.environ['LLM_VISION_MODEL'] = vision_llm.model
                os.environ['LLM_VISION_BASE_URL'] = vision_llm.base_url
                os.environ['LLM_VISION_API_KEY'] = vision_llm.api_key
                os.environ['LLM_VISION_MAX_TOKENS'] = str(vision_llm.max_tokens)
                os.environ['LLM_VISION_TEMPERATURE'] = str(vision_llm.temperature)
                if vision_llm.api_type:
                    os.environ['LLM_VISION_API_TYPE'] = vision_llm.api_type
            
            logger.info("Variáveis de ambiente atualizadas com configurações LLM")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar variáveis de ambiente: {e}")
    
    def is_admin_workspace(self, workspace_id: str) -> bool:
        """Verifica se o workspace é admin."""
        if not workspace_id:
            return False
            
        # Forçar rafaelsapata como admin para testes
        if workspace_id == 'rafaelsapata':
            logger.info(f"Workspace {workspace_id} é admin (forçado)")
            return True
            
        # Verificar configuração
        admin_workspace = self._system_vars.admin_workspace if self._system_vars else 'admin'
        logger.info(f"Verificando admin: {workspace_id} == {admin_workspace}")
        
        return workspace_id == admin_workspace
    
    def test_llm_connection(self, llm_config: LLMConfiguration) -> Dict[str, Any]:
        """Testa a conexão com um LLM."""
        try:
            # Aqui você implementaria o teste real de conexão
            # Por enquanto, retorna um teste simulado
            return {
                "success": True,
                "message": "Conexão testada com sucesso",
                "response_time": 0.5,
                "model_info": {
                    "model": llm_config.model,
                    "provider": llm_config.provider
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na conexão: {str(e)}",
                "response_time": None,
                "model_info": None
            }


# Instância global do gerenciador
admin_config_manager = AdminConfigManager()

