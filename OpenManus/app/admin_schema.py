"""
OUDS - Admin Configuration Schema
================================

Esquemas de dados para configurações administrativas.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LLMType(str, Enum):
    """Tipos de LLM suportados."""
    TEXT = "text"
    VISION = "vision"


class LLMProvider(str, Enum):
    """Provedores de LLM suportados."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class LLMStatus(str, Enum):
    """Status de conexão do LLM."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class LLMConfiguration(BaseModel):
    """Configuração de um LLM."""
    id: str = Field(..., description="ID único da configuração")
    llm_type: LLMType = Field(..., description="Tipo do LLM (text ou vision)")
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="Provedor do LLM")
    model: str = Field(..., description="Nome do modelo")
    base_url: str = Field(..., description="URL base da API")
    api_key: str = Field(..., description="Chave da API")
    api_type: Optional[str] = Field(default=None, description="Tipo da API (opcional)")
    max_tokens: int = Field(default=8192, description="Máximo de tokens")
    temperature: float = Field(default=0.0, description="Temperatura do modelo")
    status: LLMStatus = Field(default=LLMStatus.INACTIVE, description="Status da conexão")
    is_default: bool = Field(default=False, description="Se é a configuração padrão")
    last_test: Optional[str] = Field(default=None, description="Último teste de conexão")
    created_at: Optional[str] = Field(default=None, description="Data de criação")
    updated_at: Optional[str] = Field(default=None, description="Data de atualização")


class SystemVariables(BaseModel):
    """Variáveis do sistema carregadas."""
    admin_workspace: Optional[str] = Field(default=None, description="Workspace administrativo")
    llm_text: Optional[LLMConfiguration] = Field(default=None, description="Configuração LLM texto")
    llm_vision: Optional[LLMConfiguration] = Field(default=None, description="Configuração LLM visão")
    environment: str = Field(default="development", description="Ambiente de execução")
    debug_mode: bool = Field(default=False, description="Modo debug ativo")


class LogEntry(BaseModel):
    """Entrada de log do sistema."""
    timestamp: str = Field(..., description="Timestamp do log")
    level: str = Field(..., description="Nível do log")
    source: str = Field(..., description="Origem do log (frontend/backend)")
    message: str = Field(..., description="Mensagem do log")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes adicionais")


class DebugInfo(BaseModel):
    """Informações de debug do sistema."""
    system_variables: SystemVariables = Field(..., description="Variáveis do sistema")
    frontend_logs: List[LogEntry] = Field(default_factory=list, description="Logs do frontend")
    backend_logs: List[LogEntry] = Field(default_factory=list, description="Logs do backend")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de performance")
    active_connections: int = Field(default=0, description="Conexões ativas")


class AdminConfigRequest(BaseModel):
    """Requisição de configuração administrativa."""
    llm_text: Optional[LLMConfiguration] = Field(default=None, description="Configuração LLM texto")
    llm_vision: Optional[LLMConfiguration] = Field(default=None, description="Configuração LLM visão")
    reload_system: bool = Field(default=True, description="Recarregar sistema após alteração")


class AdminConfigResponse(BaseModel):
    """Resposta de configuração administrativa."""
    success: bool = Field(..., description="Sucesso da operação")
    message: str = Field(..., description="Mensagem de retorno")
    current_config: SystemVariables = Field(..., description="Configuração atual")
    errors: Optional[List[str]] = Field(default=None, description="Erros encontrados")

