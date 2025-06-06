"""
OUDS - Log Manager
==================

Sistema de gerenciamento de logs para debug administrativo.
"""

import json
import logging
import os
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.logger import logger


class LogCapture(logging.Handler):
    """Handler personalizado para capturar logs em memória."""
    
    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()
    
    def emit(self, record):
        """Captura um log record."""
        try:
            with self.lock:
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "source": "backend",
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                    "details": {
                        "pathname": record.pathname,
                        "process": record.process,
                        "thread": record.thread
                    }
                }
                
                # Adicionar informações extras se disponíveis
                if hasattr(record, 'workspace_id'):
                    log_entry["details"]["workspace_id"] = record.workspace_id
                
                if hasattr(record, 'user_id'):
                    log_entry["details"]["user_id"] = record.user_id
                
                if record.exc_info:
                    log_entry["details"]["exception"] = self.format(record)
                
                self.logs.append(log_entry)
                
        except Exception:
            # Evitar loops infinitos se houver erro no logging
            pass
    
    def get_logs(self, limit: Optional[int] = None, level: Optional[str] = None) -> List[Dict]:
        """Retorna logs capturados."""
        with self.lock:
            logs = list(self.logs)
            
            # Filtrar por nível se especificado
            if level:
                logs = [log for log in logs if log["level"] == level.upper()]
            
            # Limitar quantidade se especificado
            if limit:
                logs = logs[-limit:]
            
            return logs
    
    def clear_logs(self):
        """Limpa todos os logs capturados."""
        with self.lock:
            self.logs.clear()


class LogManager:
    """Gerenciador central de logs para o sistema."""
    
    def __init__(self):
        self.log_capture = LogCapture(max_logs=2000)
        self.frontend_logs = deque(maxlen=500)
        self.frontend_lock = threading.Lock()
        self._setup_log_capture()
    
    def _setup_log_capture(self):
        """Configura captura de logs do sistema."""
        # Adicionar handler ao logger raiz para capturar todos os logs
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_capture)
        
        # Adicionar handler ao logger específico do OUDS
        ouds_logger = logging.getLogger("ouds")
        ouds_logger.addHandler(self.log_capture)
        
        logger.info("Sistema de captura de logs configurado")
    
    def add_frontend_log(self, log_entry: Dict[str, Any]):
        """Adiciona log do frontend."""
        try:
            with self.frontend_lock:
                # Padronizar formato do log do frontend
                standardized_log = {
                    "timestamp": log_entry.get("timestamp", datetime.now().isoformat()),
                    "level": log_entry.get("level", "INFO"),
                    "source": "frontend",
                    "message": log_entry.get("message", ""),
                    "component": log_entry.get("component", "unknown"),
                    "details": log_entry.get("details", {})
                }
                
                self.frontend_logs.append(standardized_log)
                
        except Exception as e:
            logger.error(f"Erro ao adicionar log do frontend: {e}")
    
    def get_backend_logs(self, limit: Optional[int] = None, level: Optional[str] = None) -> List[Dict]:
        """Retorna logs do backend."""
        return self.log_capture.get_logs(limit=limit, level=level)
    
    def get_frontend_logs(self, limit: Optional[int] = None, level: Optional[str] = None) -> List[Dict]:
        """Retorna logs do frontend."""
        with self.frontend_lock:
            logs = list(self.frontend_logs)
            
            # Filtrar por nível se especificado
            if level:
                logs = [log for log in logs if log["level"] == level.upper()]
            
            # Limitar quantidade se especificado
            if limit:
                logs = logs[-limit:]
            
            return logs
    
    def get_all_logs(self, limit: Optional[int] = None, level: Optional[str] = None) -> List[Dict]:
        """Retorna todos os logs (backend + frontend) ordenados por timestamp."""
        backend_logs = self.get_backend_logs(level=level)
        frontend_logs = self.get_frontend_logs(level=level)
        
        # Combinar e ordenar por timestamp
        all_logs = backend_logs + frontend_logs
        all_logs.sort(key=lambda x: x["timestamp"])
        
        # Limitar quantidade se especificado
        if limit:
            all_logs = all_logs[-limit:]
        
        return all_logs
    
    def clear_all_logs(self):
        """Limpa todos os logs."""
        self.log_capture.clear_logs()
        with self.frontend_lock:
            self.frontend_logs.clear()
        logger.info("Todos os logs foram limpos")
    
    def clear_backend_logs(self):
        """Limpa apenas logs do backend."""
        self.log_capture.clear_logs()
        logger.info("Logs do backend foram limpos")
    
    def clear_frontend_logs(self):
        """Limpa apenas logs do frontend."""
        with self.frontend_lock:
            self.frontend_logs.clear()
        logger.info("Logs do frontend foram limpos")
    
    def export_logs(self, include_backend: bool = True, include_frontend: bool = True) -> str:
        """Exporta logs para formato JSON."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "logs": []
            }
            
            if include_backend:
                export_data["logs"].extend(self.get_backend_logs())
            
            if include_frontend:
                export_data["logs"].extend(self.get_frontend_logs())
            
            # Ordenar por timestamp
            export_data["logs"].sort(key=lambda x: x["timestamp"])
            
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Erro ao exportar logs: {e}")
            return json.dumps({"error": str(e)})
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos logs."""
        try:
            backend_logs = self.get_backend_logs()
            frontend_logs = self.get_frontend_logs()
            
            # Contar por nível
            backend_levels = {}
            frontend_levels = {}
            
            for log in backend_logs:
                level = log["level"]
                backend_levels[level] = backend_levels.get(level, 0) + 1
            
            for log in frontend_logs:
                level = log["level"]
                frontend_levels[level] = frontend_levels.get(level, 0) + 1
            
            return {
                "total_logs": len(backend_logs) + len(frontend_logs),
                "backend": {
                    "total": len(backend_logs),
                    "by_level": backend_levels
                },
                "frontend": {
                    "total": len(frontend_logs),
                    "by_level": frontend_levels
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas dos logs: {e}")
            return {"error": str(e)}


# Instância global do gerenciador de logs
log_manager = LogManager()

