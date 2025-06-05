"""
OUDS - Sistema de Evolução e Aprendizado Contínuo
===============================================

Este módulo implementa o sistema de aprendizado automático que evolui
a base de conhecimento baseado nas conversas e interações.
"""

import json
import re
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import hashlib
from collections import Counter, defaultdict

from .workspace_knowledge import KnowledgeEntry, ConversationRecord, knowledge_manager
from .llm_router import llm_router, ContextType

logger = logging.getLogger(__name__)

@dataclass
class LearningPattern:
    """Representa um padrão aprendido"""
    id: str
    pattern_type: str  # fact, preference, behavior, context
    content: str
    confidence: float
    evidence_count: int
    first_seen: str
    last_seen: str
    workspace_id: str
    source_conversations: List[str]

@dataclass
class LearningInsight:
    """Representa um insight de aprendizado"""
    insight_type: str
    description: str
    confidence: float
    supporting_evidence: List[str]
    recommended_action: str

class ConversationAnalyzer:
    """Analisador de conversas para extração de conhecimento"""
    
    def __init__(self):
        self.fact_patterns = [
            r"(?:eu|meu|minha|nosso|nossa)\s+(.+?)\s+(?:é|são|foi|eram|será)\s+(.+)",
            r"(.+?)\s+(?:funciona|trabalha|opera)\s+(?:com|usando|através de)\s+(.+)",
            r"(?:para|quando)\s+(.+?),?\s+(?:use|utilize|faça|execute)\s+(.+)",
            r"(.+?)\s+(?:está localizado|fica|encontra-se)\s+(?:em|no|na)\s+(.+)"
        ]
        
        self.preference_patterns = [
            r"(?:eu|nós)\s+(?:prefiro|preferimos|gosto|gostamos)\s+(.+)",
            r"(?:eu|nós)\s+(?:não gosto|não gostamos|odeio|odiamos)\s+(.+)",
            r"(?:sempre|geralmente|normalmente)\s+(?:uso|utilizo|faço)\s+(.+)",
            r"(?:nunca|jamais)\s+(?:uso|utilizo|faço)\s+(.+)"
        ]
        
        self.context_patterns = [
            r"(?:quando|se)\s+(.+?),?\s+(?:então|aí|depois)\s+(.+)",
            r"(?:antes de|após|depois de)\s+(.+?),?\s+(?:eu|nós)\s+(.+)",
            r"(?:no contexto de|durante|enquanto)\s+(.+?),?\s+(.+)"
        ]
    
    def analyze_conversation(self, conversation: ConversationRecord) -> List[LearningPattern]:
        """Analisa uma conversa e extrai padrões de aprendizado"""
        patterns = []
        
        # Analisar mensagem do usuário
        user_patterns = self._extract_patterns_from_text(
            conversation.user_message, 
            conversation.id,
            conversation.workspace_id if hasattr(conversation, 'workspace_id') else 'default'
        )
        patterns.extend(user_patterns)
        
        # Analisar resposta do assistente para validar conhecimento
        assistant_patterns = self._extract_validated_knowledge(
            conversation.assistant_response,
            conversation.user_message,
            conversation.id,
            conversation.workspace_id if hasattr(conversation, 'workspace_id') else 'default'
        )
        patterns.extend(assistant_patterns)
        
        return patterns
    
    def _extract_patterns_from_text(self, text: str, conversation_id: str, workspace_id: str) -> List[LearningPattern]:
        """Extrai padrões de um texto"""
        patterns = []
        text_lower = text.lower()
        
        # Extrair fatos
        for pattern in self.fact_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    subject = match.group(1).strip()
                    predicate = match.group(2).strip()
                    
                    if len(subject) > 2 and len(predicate) > 2:
                        content = f"{subject} -> {predicate}"
                        pattern_obj = self._create_learning_pattern(
                            "fact", content, conversation_id, workspace_id
                        )
                        patterns.append(pattern_obj)
        
        # Extrair preferências
        for pattern in self.preference_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                preference = match.group(1).strip()
                if len(preference) > 2:
                    pattern_obj = self._create_learning_pattern(
                        "preference", preference, conversation_id, workspace_id
                    )
                    patterns.append(pattern_obj)
        
        # Extrair contextos
        for pattern in self.context_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    condition = match.group(1).strip()
                    action = match.group(2).strip()
                    
                    if len(condition) > 2 and len(action) > 2:
                        content = f"SE {condition} ENTÃO {action}"
                        pattern_obj = self._create_learning_pattern(
                            "context", content, conversation_id, workspace_id
                        )
                        patterns.append(pattern_obj)
        
        return patterns
    
    def _extract_validated_knowledge(self, assistant_response: str, user_message: str, 
                                   conversation_id: str, workspace_id: str) -> List[LearningPattern]:
        """Extrai conhecimento validado da resposta do assistente"""
        patterns = []
        
        # Procurar por definições e explicações
        definition_patterns = [
            r"(.+?)\s+(?:é|são)\s+(.+?)(?:\.|$)",
            r"(.+?)\s+(?:significa|representa)\s+(.+?)(?:\.|$)",
            r"(?:definição|conceito):\s*(.+?)(?:\.|$)"
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, assistant_response, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    term = match.group(1).strip()
                    definition = match.group(2).strip()
                    
                    if len(term) > 2 and len(definition) > 10:
                        content = f"DEFINIÇÃO: {term} = {definition}"
                        pattern_obj = self._create_learning_pattern(
                            "fact", content, conversation_id, workspace_id, confidence=0.9
                        )
                        patterns.append(pattern_obj)
        
        # Procurar por procedimentos e instruções
        procedure_patterns = [
            r"(?:para|como)\s+(.+?),?\s+(?:você deve|faça|execute|siga)\s+(.+?)(?:\.|$)",
            r"(?:passos?|etapas?)\s+(?:para|de)\s+(.+?):\s*(.+?)(?:\.|$)"
        ]
        
        for pattern in procedure_patterns:
            matches = re.finditer(pattern, assistant_response, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    task = match.group(1).strip()
                    procedure = match.group(2).strip()
                    
                    if len(task) > 2 and len(procedure) > 10:
                        content = f"PROCEDIMENTO: {task} -> {procedure}"
                        pattern_obj = self._create_learning_pattern(
                            "behavior", content, conversation_id, workspace_id, confidence=0.8
                        )
                        patterns.append(pattern_obj)
        
        return patterns
    
    def _create_learning_pattern(self, pattern_type: str, content: str, 
                               conversation_id: str, workspace_id: str, 
                               confidence: float = 0.7) -> LearningPattern:
        """Cria um padrão de aprendizado"""
        now = datetime.now(timezone.utc).isoformat()
        pattern_id = hashlib.md5(f"{workspace_id}:{pattern_type}:{content}".encode()).hexdigest()
        
        return LearningPattern(
            id=pattern_id,
            pattern_type=pattern_type,
            content=content,
            confidence=confidence,
            evidence_count=1,
            first_seen=now,
            last_seen=now,
            workspace_id=workspace_id,
            source_conversations=[conversation_id]
        )

class KnowledgeEvolutionEngine:
    """Motor de evolução do conhecimento"""
    
    def __init__(self):
        self.analyzer = ConversationAnalyzer()
        self.learning_patterns: Dict[str, Dict[str, LearningPattern]] = defaultdict(dict)
        self.evolution_log_path = Path("/home/ubuntu/ouds-project/workspace_knowledge")
    
    async def process_conversation(self, conversation: ConversationRecord, workspace_id: str):
        """Processa uma conversa para aprendizado"""
        try:
            # Extrair padrões da conversa
            patterns = self.analyzer.analyze_conversation(conversation)
            
            # Processar cada padrão
            for pattern in patterns:
                await self._process_learning_pattern(pattern, workspace_id)
            
            # Registrar conversa no log de evolução
            self._log_evolution_event(workspace_id, "conversation_processed", {
                "conversation_id": conversation.id,
                "patterns_extracted": len(patterns),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro ao processar conversa para aprendizado: {e}")
    
    async def _process_learning_pattern(self, pattern: LearningPattern, workspace_id: str):
        """Processa um padrão de aprendizado"""
        # Verificar se padrão já existe
        existing_pattern = self.learning_patterns[workspace_id].get(pattern.id)
        
        if existing_pattern:
            # Atualizar padrão existente
            existing_pattern.evidence_count += 1
            existing_pattern.last_seen = pattern.last_seen
            existing_pattern.confidence = min(1.0, existing_pattern.confidence + 0.1)
            existing_pattern.source_conversations.extend(pattern.source_conversations)
        else:
            # Adicionar novo padrão
            self.learning_patterns[workspace_id][pattern.id] = pattern
        
        # Se confiança é alta o suficiente, adicionar à base de conhecimento
        final_pattern = existing_pattern or pattern
        if final_pattern.confidence >= 0.8 and final_pattern.evidence_count >= 2:
            await self._promote_to_knowledge_base(final_pattern, workspace_id)
    
    async def _promote_to_knowledge_base(self, pattern: LearningPattern, workspace_id: str):
        """Promove um padrão para a base de conhecimento"""
        try:
            # Criar entrada de conhecimento
            knowledge_entry = KnowledgeEntry.create(
                content=pattern.content,
                type=pattern.pattern_type,
                source="learned",
                confidence=pattern.confidence,
                tags=[pattern.pattern_type, "auto_learned"]
            )
            
            # Adicionar à base de conhecimento
            success = knowledge_manager.add_knowledge(workspace_id, knowledge_entry)
            
            if success:
                logger.info(f"Conhecimento promovido para workspace {workspace_id}: {pattern.content[:50]}...")
                
                # Registrar promoção
                self._log_evolution_event(workspace_id, "knowledge_promoted", {
                    "pattern_id": pattern.id,
                    "pattern_type": pattern.pattern_type,
                    "confidence": pattern.confidence,
                    "evidence_count": pattern.evidence_count,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            logger.error(f"Erro ao promover padrão para base de conhecimento: {e}")
    
    def _log_evolution_event(self, workspace_id: str, event_type: str, data: Dict[str, Any]):
        """Registra evento de evolução"""
        try:
            log_file = self.evolution_log_path / workspace_id / "evolution_log.json"
            log_file.parent.mkdir(exist_ok=True)
            
            # Carregar log existente
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            else:
                log_data = {"events": []}
            
            # Adicionar novo evento
            event = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            log_data["events"].append(event)
            
            # Manter apenas os últimos 1000 eventos
            if len(log_data["events"]) > 1000:
                log_data["events"] = log_data["events"][-1000:]
            
            # Salvar log
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao registrar evento de evolução: {e}")
    
    async def analyze_workspace_evolution(self, workspace_id: str) -> List[LearningInsight]:
        """Analisa a evolução de um workspace e gera insights"""
        insights = []
        
        try:
            # Obter estatísticas do workspace
            stats = knowledge_manager.get_workspace_stats(workspace_id)
            
            # Analisar crescimento do conhecimento
            if stats.get("total_knowledge_entries", 0) > 0:
                avg_usage = stats.get("avg_knowledge_usage", 0)
                
                if avg_usage < 1.0:
                    insights.append(LearningInsight(
                        insight_type="low_usage",
                        description="Base de conhecimento tem baixo uso médio",
                        confidence=0.8,
                        supporting_evidence=[f"Uso médio: {avg_usage:.2f}"],
                        recommended_action="Revisar relevância do conhecimento armazenado"
                    ))
                
                if avg_usage > 5.0:
                    insights.append(LearningInsight(
                        insight_type="high_usage",
                        description="Base de conhecimento é muito utilizada",
                        confidence=0.9,
                        supporting_evidence=[f"Uso médio: {avg_usage:.2f}"],
                        recommended_action="Expandir conhecimento em áreas relacionadas"
                    ))
            
            # Analisar padrões de aprendizado
            workspace_patterns = self.learning_patterns.get(workspace_id, {})
            if workspace_patterns:
                pattern_types = Counter(p.pattern_type for p in workspace_patterns.values())
                
                for pattern_type, count in pattern_types.items():
                    if count > 10:
                        insights.append(LearningInsight(
                            insight_type="pattern_trend",
                            description=f"Alto volume de padrões do tipo '{pattern_type}'",
                            confidence=0.7,
                            supporting_evidence=[f"{count} padrões identificados"],
                            recommended_action=f"Otimizar processamento de {pattern_type}"
                        ))
            
            # Analisar log de evolução
            evolution_insights = await self._analyze_evolution_log(workspace_id)
            insights.extend(evolution_insights)
            
        except Exception as e:
            logger.error(f"Erro ao analisar evolução do workspace: {e}")
        
        return insights
    
    async def _analyze_evolution_log(self, workspace_id: str) -> List[LearningInsight]:
        """Analisa o log de evolução para gerar insights"""
        insights = []
        
        try:
            log_file = self.evolution_log_path / workspace_id / "evolution_log.json"
            if not log_file.exists():
                return insights
            
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            events = log_data.get("events", [])
            if not events:
                return insights
            
            # Analisar últimos 30 dias
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            recent_events = [
                e for e in events 
                if datetime.fromisoformat(e["timestamp"].replace('Z', '+00:00')) > cutoff_date
            ]
            
            if not recent_events:
                insights.append(LearningInsight(
                    insight_type="no_recent_activity",
                    description="Nenhuma atividade de aprendizado nos últimos 30 dias",
                    confidence=0.9,
                    supporting_evidence=["Log de evolução vazio"],
                    recommended_action="Verificar se o sistema de aprendizado está funcionando"
                ))
                return insights
            
            # Analisar frequência de eventos
            event_types = Counter(e["event_type"] for e in recent_events)
            
            conversations_processed = event_types.get("conversation_processed", 0)
            knowledge_promoted = event_types.get("knowledge_promoted", 0)
            
            if conversations_processed > 0:
                promotion_rate = knowledge_promoted / conversations_processed
                
                if promotion_rate < 0.1:
                    insights.append(LearningInsight(
                        insight_type="low_learning_rate",
                        description="Taxa de aprendizado baixa",
                        confidence=0.8,
                        supporting_evidence=[
                            f"{conversations_processed} conversas processadas",
                            f"{knowledge_promoted} conhecimentos promovidos",
                            f"Taxa: {promotion_rate:.2%}"
                        ],
                        recommended_action="Ajustar critérios de promoção de conhecimento"
                    ))
                
                if promotion_rate > 0.5:
                    insights.append(LearningInsight(
                        insight_type="high_learning_rate",
                        description="Taxa de aprendizado muito alta",
                        confidence=0.8,
                        supporting_evidence=[
                            f"{conversations_processed} conversas processadas",
                            f"{knowledge_promoted} conhecimentos promovidos",
                            f"Taxa: {promotion_rate:.2%}"
                        ],
                        recommended_action="Verificar qualidade do conhecimento aprendido"
                    ))
        
        except Exception as e:
            logger.error(f"Erro ao analisar log de evolução: {e}")
        
        return insights
    
    async def cleanup_learning_patterns(self, workspace_id: str, days_threshold: int = 30):
        """Limpa padrões de aprendizado antigos e não promovidos"""
        try:
            workspace_patterns = self.learning_patterns.get(workspace_id, {})
            if not workspace_patterns:
                return 0
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
            patterns_to_remove = []
            
            for pattern_id, pattern in workspace_patterns.items():
                last_seen = datetime.fromisoformat(pattern.last_seen.replace('Z', '+00:00'))
                
                # Remover se é antigo e tem baixa confiança
                if last_seen < cutoff_date and pattern.confidence < 0.6:
                    patterns_to_remove.append(pattern_id)
            
            # Remover padrões identificados
            for pattern_id in patterns_to_remove:
                del workspace_patterns[pattern_id]
            
            logger.info(f"Removidos {len(patterns_to_remove)} padrões antigos do workspace {workspace_id}")
            return len(patterns_to_remove)
            
        except Exception as e:
            logger.error(f"Erro ao limpar padrões de aprendizado: {e}")
            return 0

# Instância global do motor de evolução
evolution_engine = KnowledgeEvolutionEngine()

