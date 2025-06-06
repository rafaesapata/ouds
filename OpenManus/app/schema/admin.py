"""
OUDS - Admin Configuration Schema
================================

Esquemas de dados para configurações administrativas e LLM.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class LLMType(str, Enum):
    """Tipos de LLM."""
    TEXT = "text"
    VISION = "vision"

class LLMProvider(str, Enum):
    """Provedores de LLM suportados."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"

class LLMStatus(str, Enum):
    """Status do LLM."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"

class LLMConfiguration(BaseModel):
    """Configuração de um LLM."""
    id: str = Field(..., description="ID único do LLM")
    name: str = Field(..., description="Nome amigável do LLM")
    type: LLMType = Field(..., description="Tipo do LLM (text/vision)")
    provider: LLMProvider = Field(..., description="Provedor do LLM")
    model: str = Field(..., description="Nome do modelo")
    base_url: str = Field(..., description="URL base da API")
    api_key: str = Field(..., description="Chave da API")
    api_type: Optional[str] = Field(None, description="Tipo da API (opcional)")
    max_tokens: int = Field(4096, description="Máximo de tokens")
    temperature: float = Field(0.7, description="Temperatura do modelo")
    status: LLMStatus = Field(LLMStatus.INACTIVE, description="Status atual")
    is_default: bool = Field(False, description="Se é o LLM padrão para seu tipo")
    created_at: str = Field(..., description="Data de criação")
    updated_at: str = Field(..., description="Data de atualização")

class SystemVariables(BaseModel):
    """Variáveis do sistema."""
    admin_workspace: str = Field(..., description="Workspace do administrador")
    workspace_root: str = Field(..., description="Diretório raiz do workspace")
    log_level: str = Field(..., description="Nível de log")
    github_token: Optional[str] = Field(None, description="Token do GitHub")
    environment: str = Field("development", description="Ambiente atual")
    version: str = Field("1.0.0", description="Versão do sistema")

class LogEntry(BaseModel):
    """Entrada de log."""
    timestamp: str = Field(..., description="Timestamp do log")
    level: str = Field(..., description="Nível do log")
    source: str = Field(..., description="Fonte do log (frontend/backend)")
    message: str = Field(..., description="Mensagem do log")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")

class DebugInfo(BaseModel):
    """Informações de debug."""
    system_variables: SystemVariables
    llm_configurations: List[LLMConfiguration]
    recent_logs: List[LogEntry]
    system_status: Dict[str, Any]

class AdminConfigRequest(BaseModel):
    """Request para atualizar configurações administrativas."""
    llm_configurations: Optional[List[LLMConfiguration]] = None
    system_variables: Optional[SystemVariables] = None

class AdminConfigResponse(BaseModel):
    """Response das configurações administrativas."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

