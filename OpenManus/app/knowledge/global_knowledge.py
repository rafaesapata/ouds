"""
OUDS - Sistema de Base de Conhecimento Global
============================================

Este módulo implementa o sistema de conhecimento global que é aplicado
a todos os workspaces e LLMs do sistema.
"""

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import lru_cache
import logging

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class GlobalKnowledgeEntry:
    """Representa uma entrada de conhecimento global"""
    id: str
    type: str  # directive, fact, preference, context, pattern
    content: str
    priority: str  # high, medium, low
    tags: List[str]
    
    def __post_init__(self):
        """Validação após inicialização"""
        valid_types = ["directive", "fact", "preference", "context", "pattern"]
        valid_priorities = ["high", "medium", "low"]
        
        if self.type not in valid_types:
            raise ValueError(f"Tipo inválido: {self.type}. Deve ser um de: {valid_types}")
        
        if self.priority not in valid_priorities:
            raise ValueError(f"Prioridade inválida: {self.priority}. Deve ser uma de: {valid_priorities}")
        
        if not self.content.strip():
            raise ValueError("Conteúdo não pode estar vazio")

class GlobalKnowledgeManager:
    """Gerenciador da base de conhecimento global com otimizações de performance"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        """Implementa padrão Singleton para garantir única instância"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa o gerenciador apenas uma vez"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self.knowledge_entries: Dict[str, GlobalKnowledgeEntry] = {}
                    self.entries_by_type: Dict[str, List[GlobalKnowledgeEntry]] = {}
                    self.entries_by_priority: Dict[str, List[GlobalKnowledgeEntry]] = {}
                    self.entries_by_tag: Dict[str, List[GlobalKnowledgeEntry]] = {}
                    self.last_loaded: Optional[datetime] = None
                    self.file_mtime: Optional[float] = None
                    
                    # Cache para contextos LLM
                    self._llm_context_cache: Dict[str, str] = {}
                    self._cache_timestamp: float = 0
                    self._cache_ttl: float = 300  # 5 minutos
                    
                    self._load_global_knowledge()
                    self._initialized = True
    
    def _get_config_path(self) -> Path:
        """Retorna o caminho do arquivo de configuração"""
        try:
            # Tentar usar o caminho da configuração principal
            from app.config import config
            return config.root_path / "config" / "global_knowledge.json"
        except ImportError:
            # Fallback: usar caminho relativo ao arquivo atual
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            return project_root / "config" / "global_knowledge.json"
    
    def _should_reload(self) -> bool:
        """Verifica se o arquivo foi modificado e precisa ser recarregado"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            return False
        
        try:
            current_mtime = config_path.stat().st_mtime
            return self.file_mtime is None or current_mtime > self.file_mtime
        except OSError:
            return False
    
    def _load_global_knowledge(self):
        """Carrega a base de conhecimento global do arquivo JSON"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            logger.warning(f"Arquivo de conhecimento global não encontrado: {config_path}")
            return
        
        try:
            # Verificar se precisa recarregar
            if not self._should_reload():
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Atualizar timestamp do arquivo
            self.file_mtime = config_path.stat().st_mtime
            
            # Validar estrutura básica
            if "knowledge_entries" not in data:
                logger.error("Arquivo de conhecimento global inválido: falta 'knowledge_entries'")
                return
            
            # Limpar dados existentes
            self.knowledge_entries.clear()
            self.entries_by_type.clear()
            self.entries_by_priority.clear()
            self.entries_by_tag.clear()
            
            # Limpar cache
            self._llm_context_cache.clear()
            self._cache_timestamp = 0
            
            # Carregar entradas
            for entry_data in data["knowledge_entries"]:
                try:
                    entry = GlobalKnowledgeEntry(
                        id=entry_data["id"],
                        type=entry_data["type"],
                        content=entry_data["content"],
                        priority=entry_data["priority"],
                        tags=entry_data.get("tags", [])
                    )
                    
                    # Armazenar entrada
                    self.knowledge_entries[entry.id] = entry
                    
                    # Indexar por tipo
                    if entry.type not in self.entries_by_type:
                        self.entries_by_type[entry.type] = []
                    self.entries_by_type[entry.type].append(entry)
                    
                    # Indexar por prioridade
                    if entry.priority not in self.entries_by_priority:
                        self.entries_by_priority[entry.priority] = []
                    self.entries_by_priority[entry.priority].append(entry)
                    
                    # Indexar por tags
                    for tag in entry.tags:
                        if tag not in self.entries_by_tag:
                            self.entries_by_tag[tag] = []
                        self.entries_by_tag[tag].append(entry)
                
                except Exception as e:
                    logger.error(f"Erro ao processar entrada {entry_data.get('id', 'unknown')}: {e}")
                    continue
            
            self.last_loaded = datetime.now(timezone.utc)
            logger.info(f"Base de conhecimento global carregada: {len(self.knowledge_entries)} entradas")
            
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento global: {e}")
    
    def reload_knowledge(self):
        """Recarrega a base de conhecimento do arquivo"""
        logger.info("Recarregando base de conhecimento global...")
        self.file_mtime = None  # Forçar recarregamento
        self._load_global_knowledge()
    
    def get_all_entries(self) -> List[GlobalKnowledgeEntry]:
        """Retorna todas as entradas de conhecimento"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        return list(self.knowledge_entries.values())
    
    def get_entries_by_type(self, entry_type: str) -> List[GlobalKnowledgeEntry]:
        """Retorna entradas por tipo"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        return self.entries_by_type.get(entry_type, [])
    
    def get_entries_by_priority(self, priority: str) -> List[GlobalKnowledgeEntry]:
        """Retorna entradas por prioridade"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        return self.entries_by_priority.get(priority, [])
    
    def get_entries_by_tag(self, tag: str) -> List[GlobalKnowledgeEntry]:
        """Retorna entradas por tag"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        return self.entries_by_tag.get(tag, [])
    
    def get_entry_by_id(self, entry_id: str) -> Optional[GlobalKnowledgeEntry]:
        """Retorna uma entrada específica por ID"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        return self.knowledge_entries.get(entry_id)
    
    @lru_cache(maxsize=128)
    def search_entries(self, query: str, limit: int = 10) -> List[GlobalKnowledgeEntry]:
        """Busca entradas por conteúdo ou tags (com cache)"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        
        query_lower = query.lower()
        results = []
        
        for entry in self.knowledge_entries.values():
            # Buscar no conteúdo
            if query_lower in entry.content.lower():
                results.append(entry)
                continue
            
            # Buscar nas tags
            for tag in entry.tags:
                if query_lower in tag.lower():
                    results.append(entry)
                    break
        
        # Ordenar por prioridade (high > medium > low)
        priority_order = {"high": 3, "medium": 2, "low": 1}
        results.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
        
        return results[:limit]
    
    def get_directives(self) -> List[GlobalKnowledgeEntry]:
        """Retorna todas as diretrizes do sistema"""
        return self.get_entries_by_type("directive")
    
    def get_high_priority_entries(self) -> List[GlobalKnowledgeEntry]:
        """Retorna entradas de alta prioridade"""
        return self.get_entries_by_priority("high")
    
    def get_context_for_llm(self, include_types: List[str] = None, 
                           max_entries: int = 20) -> str:
        """Gera contexto formatado para LLMs (com cache)"""
        # Verificar cache
        current_time = time.time()
        cache_key = f"{include_types}_{max_entries}"
        
        if (cache_key in self._llm_context_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._llm_context_cache[cache_key]
        
        # Verificar se precisa recarregar
        self._load_global_knowledge()
        
        if include_types is None:
            include_types = ["directive", "fact", "preference", "context", "pattern"]
        
        context_parts = []
        entry_count = 0
        
        # Priorizar entradas de alta prioridade
        for priority in ["high", "medium", "low"]:
            if entry_count >= max_entries:
                break
            
            for entry in self.get_entries_by_priority(priority):
                if entry_count >= max_entries:
                    break
                
                if entry.type in include_types:
                    context_parts.append(f"[{entry.type.upper()}] {entry.content}")
                    entry_count += 1
        
        if context_parts:
            result = "INSTRUÇÕES GLOBAIS DO SISTEMA:\\n\\n" + "\\n".join(context_parts) + "\\n\\nVocê DEVE seguir todas as instruções acima em todas as suas interações."
        else:
            result = ""
        
        # Atualizar cache
        self._llm_context_cache[cache_key] = result
        self._cache_timestamp = current_time
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da base de conhecimento"""
        self._load_global_knowledge()  # Verificar se precisa recarregar
        
        stats = {
            "total_entries": len(self.knowledge_entries),
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "file_mtime": self.file_mtime,
            "cache_size": len(self._llm_context_cache),
            "cache_ttl": self._cache_ttl,
            "entries_by_type": {
                entry_type: len(entries) 
                for entry_type, entries in self.entries_by_type.items()
            },
            "entries_by_priority": {
                priority: len(entries) 
                for priority, entries in self.entries_by_priority.items()
            },
            "total_tags": len(self.entries_by_tag),
            "most_common_tags": sorted(
                [(tag, len(entries)) for tag, entries in self.entries_by_tag.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        return stats
    
    def validate_knowledge_file(self) -> Dict[str, Any]:
        """Valida o arquivo de conhecimento e retorna relatório"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            return {
                "valid": False,
                "error": f"Arquivo não encontrado: {config_path}",
                "warnings": [],
                "stats": {}
            }
        
        warnings = []
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar estrutura
            required_fields = ["version", "knowledge_entries"]
            for field in required_fields:
                if field not in data:
                    return {
                        "valid": False,
                        "error": f"Campo obrigatório ausente: {field}",
                        "warnings": warnings,
                        "stats": {}
                    }
            
            # Validar entradas
            entry_ids = set()
            valid_entries = 0
            
            for i, entry_data in enumerate(data["knowledge_entries"]):
                try:
                    # Verificar campos obrigatórios
                    required_entry_fields = ["id", "type", "content", "priority"]
                    for field in required_entry_fields:
                        if field not in entry_data:
                            warnings.append(f"Entrada {i}: campo '{field}' ausente")
                            continue
                    
                    # Verificar ID único
                    entry_id = entry_data.get("id")
                    if entry_id in entry_ids:
                        warnings.append(f"Entrada {i}: ID duplicado '{entry_id}'")
                    else:
                        entry_ids.add(entry_id)
                    
                    # Tentar criar entrada para validação
                    GlobalKnowledgeEntry(
                        id=entry_data["id"],
                        type=entry_data["type"],
                        content=entry_data["content"],
                        priority=entry_data["priority"],
                        tags=entry_data.get("tags", [])
                    )
                    valid_entries += 1
                    
                except Exception as e:
                    warnings.append(f"Entrada {i}: {str(e)}")
            
            stats = {
                "total_entries": len(data["knowledge_entries"]),
                "valid_entries": valid_entries,
                "invalid_entries": len(data["knowledge_entries"]) - valid_entries,
                "unique_ids": len(entry_ids)
            }
            
            return {
                "valid": True,
                "error": None,
                "warnings": warnings,
                "stats": stats
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Erro de JSON: {str(e)}",
                "warnings": warnings,
                "stats": {}
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Erro inesperado: {str(e)}",
                "warnings": warnings,
                "stats": {}
            }

# Instância global do gerenciador
global_knowledge = GlobalKnowledgeManager()

def get_global_knowledge() -> GlobalKnowledgeManager:
    """Retorna a instância global do gerenciador de conhecimento"""
    return global_knowledge

def get_system_context_for_llm(max_entries: int = 20) -> str:
    """Função de conveniência para obter contexto do sistema para LLMs"""
    return global_knowledge.get_context_for_llm(max_entries=max_entries)

