"""
OUDS - API Module
================

Módulo de API com endpoints organizados.
"""

from .admin import router as admin_router

__all__ = ["admin_router"]

