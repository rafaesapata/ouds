"""
OUDS - Settings Module
======================

This module provides application settings.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings"""
    
    # Server settings
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Enable auto-reload")
    log_level: str = Field("INFO", description="Log level")
    
    # Workspace settings
    workspace_dir: str = Field("workspace", description="Workspace directory")
    
    # API settings
    api_prefix: str = Field("/api", description="API prefix")
    
    # Security settings
    secret_key: str = Field("secret", description="Secret key")
    
    # Other settings
    debug: bool = Field(False, description="Debug mode")


# Create settings instance
settings = Settings()

# Ensure workspace directory exists
Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)

