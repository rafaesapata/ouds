"""
OUDS - Settings Module
======================

This module provides application settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings with environment variable support"""
    
    # Server settings
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Enable auto-reload")
    log_level: str = Field("INFO", description="Log level")
    
    # Workspace settings
    workspace_dir: str = Field("workspace", description="Workspace directory")
    workspace_root: str = Field("./workspace", description="Workspace root directory")
    
    # Admin settings
    admin_workspace: str = Field("admin", description="Admin workspace name")
    
    # API settings
    api_prefix: str = Field("/api", description="API prefix")
    
    # Security settings
    secret_key: str = Field("secret", description="Secret key")
    
    # OpenAI Legacy (for backward compatibility)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    
    # LLM Text Configuration
    llm_api_type: Optional[str] = Field(None, description="LLM API type")
    llm_model: str = Field("gpt-4", description="LLM model name")
    llm_base_url: str = Field("https://api.openai.com/v1", description="LLM base URL")
    llm_api_key: str = Field("", description="LLM API key")
    llm_max_tokens: int = Field(4096, description="LLM max tokens")
    llm_temperature: float = Field(0.7, description="LLM temperature")
    
    # LLM Vision Configuration
    llm_vision_api_type: Optional[str] = Field(None, description="Vision LLM API type")
    llm_vision_model: str = Field("gpt-4-vision-preview", description="Vision LLM model name")
    llm_vision_base_url: str = Field("https://api.openai.com/v1", description="Vision LLM base URL")
    llm_vision_api_key: str = Field("", description="Vision LLM API key")
    llm_vision_max_tokens: int = Field(4096, description="Vision LLM max tokens")
    llm_vision_temperature: float = Field(0.7, description="Vision LLM temperature")
    
    # GitHub settings
    github_token: Optional[str] = Field(None, description="GitHub token")
    
    # Other settings
    debug: bool = Field(False, description="Debug mode")
    
    def __init__(self, **kwargs):
        # Load from environment variables
        env_values = {}
        
        # Map environment variables to settings
        env_mapping = {
            'HOST': 'host',
            'PORT': 'port',
            'LOG_LEVEL': 'log_level',
            'WORKSPACE_DIR': 'workspace_dir',
            'WORKSPACE_ROOT': 'workspace_root',
            'ADMIN_WORKSPACE': 'admin_workspace',
            'SECRET_KEY': 'secret_key',
            'OPENAI_API_KEY': 'openai_api_key',
            'LLM_API_TYPE': 'llm_api_type',
            'LLM_MODEL': 'llm_model',
            'LLM_BASE_URL': 'llm_base_url',
            'LLM_API_KEY': 'llm_api_key',
            'LLM_MAX_TOKENS': 'llm_max_tokens',
            'LLM_TEMPERATURE': 'llm_temperature',
            'LLM_VISION_API_TYPE': 'llm_vision_api_type',
            'LLM_VISION_MODEL': 'llm_vision_model',
            'LLM_VISION_BASE_URL': 'llm_vision_base_url',
            'LLM_VISION_API_KEY': 'llm_vision_api_key',
            'LLM_VISION_MAX_TOKENS': 'llm_vision_max_tokens',
            'LLM_VISION_TEMPERATURE': 'llm_vision_temperature',
            'GITHUB_TOKEN': 'github_token',
            'DEBUG': 'debug'
        }
        
        for env_key, setting_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Convert types as needed
                if setting_key in ['port', 'llm_max_tokens', 'llm_vision_max_tokens']:
                    try:
                        env_values[setting_key] = int(env_value)
                    except ValueError:
                        pass
                elif setting_key in ['llm_temperature', 'llm_vision_temperature']:
                    try:
                        env_values[setting_key] = float(env_value)
                    except ValueError:
                        pass
                elif setting_key in ['reload', 'debug']:
                    env_values[setting_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                else:
                    env_values[setting_key] = env_value
        
        # Merge with provided kwargs
        env_values.update(kwargs)
        
        super().__init__(**env_values)


# Create settings instance
settings = Settings()

# Ensure workspace directory exists
Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
Path(settings.workspace_root).mkdir(parents=True, exist_ok=True)

