"""
OUDS - Sistema de Base de Conhecimento por Workspace
==================================================

Este módulo implementa o sistema de conhecimento individual por workspace
com suporte a evolução temporal e múltiplas LLMs.
"""

import json
import os
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeEntry:
    """Representa uma entrada de conhecimento"""
    id: str
    type: str  # fact, pattern, preference, context
    content: str
    confidence: float
    source: str  # conversation, manual, learned
    created_at: str
    last_used: str
    usage_count: int
    tags: List[str]
    embedding_id: Optional[str] = None
    
    @classmethod
    def create(cls, content: str, type: str = "fact", source: str = "conversation", 
               confidence: float = 1.0, tags: List[str] = None) -> 'KnowledgeEntry':
        """Cria uma nova entrada de conhecimento"""
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            content=content,
            confidence=confidence,
            source=source,
            created_at=now,
            last_used=now,
            usage_count=0,
            tags=tags or []
        )

@dataclass
class KnowledgeRelationship:
    """Representa uma relação entre conhecimentos"""
    from_id: str
    to_id: str
    type: str  # related, contradicts, supports
    strength: float

@dataclass
class ConversationRecord:
    """Representa um registro de conversa"""
    id: str
    timestamp: str
    user_message: str
    assistant_response: str
    llm_used: str
    context_retrieved: List[str]
    knowledge_learned: List[str]
    satisfaction_score: Optional[float] = None
    processing_time: Optional[float] = None

class WorkspaceKnowledgeManager:
    """Gerenciador de conhecimento por workspace"""
    
    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            # Detectar caminho dinamicamente baseado na configuração
            try:
                from app.config import config
                self.base_path = config.workspace_root / "knowledge"
            except ImportError:
                # Fallback: usar caminho relativo ao arquivo atual
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent.parent
                self.base_path = project_root / "workspace" / "knowledge"
        else:
            self.base_path = Path(base_path)
        
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_workspace_path(self, workspace_id: str) -> Path:
        """Retorna o caminho do workspace"""
        workspace_path = self.base_path / workspace_id
        workspace_path.mkdir(exist_ok=True)
        return workspace_path
    
    def _get_knowledge_file(self, workspace_id: str) -> Path:
        """Retorna o arquivo de conhecimento do workspace"""
        return self._get_workspace_path(workspace_id) / "knowledge_base.json"
    
    def _get_conversation_file(self, workspace_id: str) -> Path:
        """Retorna o arquivo de conversas do workspace"""
        return self._get_workspace_path(workspace_id) / "conversation_history.json"
    
    def _get_embeddings_db(self, workspace_id: str) -> Path:
        """Retorna o banco de embeddings do workspace"""
        return self._get_workspace_path(workspace_id) / "context_embeddings.db"
    
    def _load_knowledge_base(self, workspace_id: str) -> Dict[str, Any]:
        """Carrega a base de conhecimento do workspace"""
        knowledge_file = self._get_knowledge_file(workspace_id)
        
        if not knowledge_file.exists():
            # Criar base de conhecimento inicial
            initial_kb = {
                "workspace_id": workspace_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
                "knowledge_entries": [],
                "relationships": []
            }
            self._save_knowledge_base(workspace_id, initial_kb)
            return initial_kb
        
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento: {e}")
            return self._load_knowledge_base(workspace_id)  # Recriar se corrompido
    
    def _save_knowledge_base(self, workspace_id: str, knowledge_base: Dict[str, Any]):
        """Salva a base de conhecimento do workspace"""
        knowledge_file = self._get_knowledge_file(workspace_id)
        knowledge_base["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        try:
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar base de conhecimento: {e}")
            raise
    
    def add_knowledge(self, workspace_id: str, entry: KnowledgeEntry) -> bool:
        """Adiciona uma entrada de conhecimento"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            
            # Verificar se já existe conhecimento similar
            existing = self._find_similar_knowledge(kb, entry.content)
            if existing:
                # Atualizar conhecimento existente
                for i, existing_entry in enumerate(kb["knowledge_entries"]):
                    if existing_entry["id"] == existing["id"]:
                        existing_entry["confidence"] = max(existing_entry["confidence"], entry.confidence)
                        existing_entry["usage_count"] += 1
                        existing_entry["last_used"] = datetime.now(timezone.utc).isoformat()
                        break
            else:
                # Adicionar novo conhecimento
                kb["knowledge_entries"].append(asdict(entry))
            
            self._save_knowledge_base(workspace_id, kb)
            logger.info(f"Conhecimento adicionado ao workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar conhecimento: {e}")
            return False
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokeniza texto em palavras-chave para busca"""
        # Remover caracteres especiais e converter para minúsculas
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Dividir em tokens e remover duplicatas
        tokens = list(set(text.split()))
        # Remover stopwords comuns em português
        stopwords = {'a', 'o', 'e', 'é', 'de', 'do', 'da', 'em', 'no', 'na', 'um', 'uma', 'que', 'para', 'com', 'por'}
        return [token for token in tokens if token not in stopwords and len(token) > 1]
    
    def search_knowledge(self, workspace_id: str, query: str, limit: int = 10) -> List[KnowledgeEntry]:
        """Busca conhecimento relevante"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            results = []
            seen_ids = set()  # Para evitar duplicatas
            
            # Tokenizar a consulta
            query_tokens = self._tokenize_text(query)
            
            # Se não há tokens válidos, usar a consulta original
            if not query_tokens:
                query_tokens = [query.lower()]
            
            # Buscar por cada token
            for entry_data in kb["knowledge_entries"]:
                # Evitar duplicatas
                if entry_data["id"] in seen_ids:
                    continue
                
                entry = KnowledgeEntry(**entry_data)
                content_lower = entry.content.lower()
                
                # Pontuação para relevância
                score = 0
                
                # Busca por tokens
                for token in query_tokens:
                    if token in content_lower:
                        score += 1
                
                # Busca por tags
                for tag in entry.tags:
                    for token in query_tokens:
                        if token in tag.lower():
                            score += 0.5
                
                # Se encontrou alguma correspondência
                if score > 0:
                    # Adicionar à lista de resultados com pontuação
                    results.append((entry, score))
                    seen_ids.add(entry.id)
            
            # Ordenar por pontuação e depois por relevância (confidence * usage_count)
            results.sort(key=lambda x: (x[1], x[0].confidence * (x[0].usage_count + 1)), reverse=True)
            
            # Extrair apenas as entradas
            entries = [entry for entry, _ in results]
            
            return entries[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento: {e}")
            return []
    
    def _find_similar_knowledge(self, kb: Dict[str, Any], content: str) -> Optional[Dict[str, Any]]:
        """Encontra conhecimento similar baseado em hash de conteúdo"""
        content_hash = hashlib.md5(content.lower().strip().encode()).hexdigest()
        
        for entry in kb["knowledge_entries"]:
            entry_hash = hashlib.md5(entry["content"].lower().strip().encode()).hexdigest()
            if content_hash == entry_hash:
                return entry
        
        return None
    
    def update_knowledge_usage(self, workspace_id: str, knowledge_id: str):
        """Atualiza estatísticas de uso do conhecimento"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            
            for entry in kb["knowledge_entries"]:
                if entry["id"] == knowledge_id:
                    entry["usage_count"] += 1
                    entry["last_used"] = datetime.now(timezone.utc).isoformat()
                    break
            
            self._save_knowledge_base(workspace_id, kb)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar uso do conhecimento: {e}")
    
    def add_conversation(self, workspace_id: str, conversation: ConversationRecord):
        """Adiciona um registro de conversa"""
        try:
            conversation_file = self._get_conversation_file(workspace_id)
            
            # Carregar histórico existente
            if conversation_file.exists():
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = {"conversations": []}
            
            # Adicionar nova conversa
            history["conversations"].append(asdict(conversation))
            
            # Manter apenas as últimas 1000 conversas
            if len(history["conversations"]) > 1000:
                history["conversations"] = history["conversations"][-1000:]
            
            # Salvar histórico
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao adicionar conversa: {e}")
    
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Retorna estatísticas do workspace"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            conversation_file = self._get_conversation_file(workspace_id)
            
            # Estatísticas da base de conhecimento
            total_knowledge = len(kb["knowledge_entries"])
            knowledge_by_type = {}
            total_usage = 0
            
            for entry in kb["knowledge_entries"]:
                entry_type = entry["type"]
                knowledge_by_type[entry_type] = knowledge_by_type.get(entry_type, 0) + 1
                total_usage += entry["usage_count"]
            
            # Estatísticas de conversas
            total_conversations = 0
            if conversation_file.exists():
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    total_conversations = len(history["conversations"])
            
            return {
                "workspace_id": workspace_id,
                "created_at": kb["created_at"],
                "last_updated": kb["last_updated"],
                "version": kb["version"],
                "total_knowledge_entries": total_knowledge,
                "knowledge_by_type": knowledge_by_type,
                "total_knowledge_usage": total_usage,
                "total_conversations": total_conversations,
                "avg_knowledge_usage": total_usage / max(total_knowledge, 1)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def cleanup_old_knowledge(self, workspace_id: str, days_threshold: int = 90):
        """Remove conhecimento antigo e pouco usado"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            now = datetime.now(timezone.utc)
            threshold = days_threshold * 24 * 60 * 60  # Converter para segundos
            
            # Filtrar entradas
            new_entries = []
            for entry in kb["knowledge_entries"]:
                try:
                    # Converter string ISO para datetime
                    created_at = datetime.fromisoformat(entry["created_at"].replace('Z', '+00:00'))
                    age_seconds = (now - created_at).total_seconds()
                    
                    # Manter se for recente ou tiver sido usado frequentemente
                    if age_seconds < threshold or entry["usage_count"] > 5:
                        new_entries.append(entry)
                except Exception:
                    # Em caso de erro, manter a entrada
                    new_entries.append(entry)
            
            # Atualizar base de conhecimento
            kb["knowledge_entries"] = new_entries
            self._save_knowledge_base(workspace_id, kb)
            
            return len(kb["knowledge_entries"])
            
        except Exception as e:
            logger.error(f"Erro ao limpar conhecimento antigo: {e}")
            return -1
    
    def get_all_entries(self, workspace_id: str) -> List[KnowledgeEntry]:
        """Retorna todas as entradas de conhecimento do workspace"""
        try:
            kb = self._load_knowledge_base(workspace_id)
            return [KnowledgeEntry(**entry_data) for entry_data in kb["knowledge_entries"]]
        except Exception as e:
            logger.error(f"Erro ao obter todas as entradas: {e}")
            return []

# Instância global do gerenciador
knowledge_manager = WorkspaceKnowledgeManager()

