"""
Configuração simplificada para o módulo de streaming de chat.
Este módulo fornece configurações básicas para o streaming de chat,
independente do sistema de configuração principal.
"""
import os
import json
import logging
from pathlib import Path

# Configurar logger
logger = logging.getLogger(__name__)

# Diretório raiz do projeto
def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent

PROJECT_ROOT = get_project_root()

# Configurações padrão
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000

# Carregar configurações do arquivo ou variáveis de ambiente
def load_config():
    """Carrega configurações para o streaming de chat"""
    config = {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        "temperature": float(os.environ.get("OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "max_tokens": int(os.environ.get("OPENAI_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
    }
    
    # Tentar carregar do arquivo de configuração
    try:
        config_path = PROJECT_ROOT / "config" / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                file_config = json.load(f)
                
                # Extrair configurações do LLM
                if "llm" in file_config:
                    llm_config = file_config["llm"]
                    if isinstance(llm_config, dict):
                        config["api_key"] = llm_config.get("api_key", config["api_key"])
                        config["api_base"] = llm_config.get("base_url", config["api_base"])
                        config["model"] = llm_config.get("model", config["model"])
                        config["temperature"] = llm_config.get("temperature", config["temperature"])
                        config["max_tokens"] = llm_config.get("max_tokens", config["max_tokens"])
    except Exception as e:
        logger.warning(f"Erro ao carregar configurações do arquivo: {e}")
    
    return config

# Carregar configurações
chat_config = load_config()

# Exportar configurações
API_KEY = chat_config["api_key"]
API_BASE = chat_config["api_base"]
MODEL = chat_config["model"]
TEMPERATURE = chat_config["temperature"]
MAX_TOKENS = chat_config["max_tokens"]

