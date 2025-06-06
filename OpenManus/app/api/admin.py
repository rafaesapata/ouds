"""
OUDS - Admin API Endpoints
==========================

Endpoints da API para funcionalidades administrativas.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.admin_config import admin_config_manager
from app.admin_schema import (
    LLMConfiguration, SystemVariables, DebugInfo, 
    AdminConfigRequest, AdminConfigResponse, LogEntry
)
from app.log_manager import log_manager
from app.logger import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_workspace(x_workspace_id: Optional[str] = Header(None)):
    """Verifica se o workspace é admin."""
    if not x_workspace_id:
        raise HTTPException(status_code=400, detail="Workspace ID required")
    
    if not admin_config_manager.is_admin_workspace(x_workspace_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return x_workspace_id


@router.get("/check")
async def check_admin_status(x_workspace_id: Optional[str] = Header(None)):
    """Verifica se o workspace atual é admin."""
    try:
        is_admin = admin_config_manager.is_admin_workspace(x_workspace_id) if x_workspace_id else False
        return {
            "success": True,
            "data": {
                "is_admin": is_admin,
                "workspace_id": x_workspace_id
            }
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status admin: {e}")
        return {"success": False, "message": str(e)}


@router.get("/config")
async def get_admin_config(workspace_id: str = Depends(verify_admin_workspace)):
    """Retorna as configurações administrativas."""
    try:
        llm_configs = admin_config_manager.get_llm_configurations()
        system_vars = admin_config_manager.get_system_variables()
        
        return {
            "success": True,
            "data": {
                "llm_configurations": [config.dict() for config in llm_configs],
                "system_variables": system_vars.dict() if system_vars else {}
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter configurações admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm")
async def update_llm_config(
    config: LLMConfiguration,
    workspace_id: str = Depends(verify_admin_workspace)
):
    """Atualiza uma configuração de LLM."""
    try:
        success = admin_config_manager.update_llm_configuration(config)
        
        if success:
            return {
                "success": True,
                "message": "Configuração LLM atualizada com sucesso",
                "data": config.dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao atualizar configuração")
            
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/llm/{llm_id}")
async def delete_llm_config(
    llm_id: str,
    workspace_id: str = Depends(verify_admin_workspace)
):
    """Remove uma configuração de LLM."""
    try:
        success = admin_config_manager.delete_llm_configuration(llm_id)
        
        if success:
            return {
                "success": True,
                "message": "Configuração LLM removida com sucesso"
            }
        else:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
            
    except Exception as e:
        logger.error(f"Erro ao remover configuração LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/test")
async def test_llm_connection(
    config: LLMConfiguration,
    workspace_id: str = Depends(verify_admin_workspace)
):
    """Testa a conexão com um LLM."""
    try:
        result = admin_config_manager.test_llm_connection(config)
        return {
            "success": result["success"],
            "message": result["message"],
            "data": result
        }
    except Exception as e:
        logger.error(f"Erro ao testar conexão LLM: {e}")
        return {
            "success": False,
            "message": f"Erro no teste: {str(e)}"
        }


@router.get("/debug")
async def get_debug_info(workspace_id: str = Depends(verify_admin_workspace)):
    """Retorna informações de debug do sistema."""
    try:
        # Logs recentes do sistema
        recent_logs = log_manager.get_all_logs(limit=50)
        
        # Converter para formato LogEntry
        log_entries = []
        for log in recent_logs:
            log_entry = LogEntry(
                timestamp=log["timestamp"],
                level=log["level"],
                source=log["source"],
                message=log["message"],
                details=log.get("details", {})
            )
            log_entries.append(log_entry)
        
        # Variáveis do sistema
        system_vars = admin_config_manager.get_system_variables()
        
        # Estatísticas dos logs
        log_stats = log_manager.get_log_statistics()
        
        # Status do sistema
        system_status = {
            "backend": {
                "status": "online",
                "uptime": "running",
                "logs_captured": log_stats.get("backend", {}).get("total", 0)
            },
            "frontend": {
                "status": "active",
                "logs_captured": log_stats.get("frontend", {}).get("total", 0)
            },
            "llm": {
                "text_configs": len([c for c in admin_config_manager.get_llm_configurations() if c.llm_type.value == "text"]),
                "vision_configs": len([c for c in admin_config_manager.get_llm_configurations() if c.llm_type.value == "vision"])
            },
            "logs": log_stats
        }
        
        debug_info = DebugInfo(
            system_variables=system_vars,
            llm_configurations=admin_config_manager.get_llm_configurations(),
            recent_logs=log_entries,
            system_status=system_status
        )
        
        return {
            "success": True,
            "data": debug_info.dict()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações de debug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/clear")
async def clear_logs(workspace_id: str = Depends(verify_admin_workspace)):
    """Limpa os logs do sistema."""
    try:
        log_manager.clear_all_logs()
        return {
            "success": True,
            "message": "Logs limpos com sucesso"
        }
    except Exception as e:
        logger.error(f"Erro ao limpar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/download")
async def download_logs(workspace_id: str = Depends(verify_admin_workspace)):
    """Baixa os logs do sistema."""
    try:
        logs_content = log_manager.export_logs()
        return {
            "success": True,
            "data": logs_content,
            "filename": f"ouds_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    except Exception as e:
        logger.error(f"Erro ao baixar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/frontend")
async def add_frontend_log(
    log_data: Dict[str, Any],
    workspace_id: str = Depends(verify_admin_workspace)
):
    """Adiciona log do frontend."""
    try:
        log_manager.add_frontend_log(log_data)
        return {
            "success": True,
            "message": "Log do frontend adicionado"
        }
    except Exception as e:
        logger.error(f"Erro ao adicionar log do frontend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stats")
async def get_log_stats(workspace_id: str = Depends(verify_admin_workspace)):
    """Retorna estatísticas dos logs."""
    try:
        stats = log_manager.get_log_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas dos logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

