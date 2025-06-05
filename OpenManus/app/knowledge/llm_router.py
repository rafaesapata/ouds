"""
OUDS - Sistema de Múltiplas LLMs com Roteamento Inteligente
=========================================================

Este módulo implementa o sistema de roteamento para múltiplas LLMs
baseado em contexto, performance e disponibilidade.
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Provedores de LLM disponíveis"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT4_TURBO = "openai_gpt4_turbo"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    ANTHROPIC_CLAUDE_SONNET = "anthropic_claude_sonnet"
    LOCAL_LLAMA = "local_llama"

class ContextType(Enum):
    """Tipos de contexto para roteamento"""
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE_WRITING = "creative_writing"
    GENERAL_CHAT = "general_chat"
    TECHNICAL_SUPPORT = "technical_support"
    RESEARCH = "research"

@dataclass
class LLMConfig:
    """Configuração de uma LLM"""
    provider: LLMProvider
    name: str
    api_endpoint: str
    api_key: str
    model_name: str
    max_tokens: int
    temperature: float
    cost_per_token: float
    rate_limit: int  # requests per minute
    timeout: int  # seconds
    enabled: bool = True

@dataclass
class LLMPerformanceMetrics:
    """Métricas de performance de uma LLM"""
    provider: LLMProvider
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    avg_tokens_per_request: float
    total_cost: float
    last_used: str
    uptime_percentage: float

@dataclass
class RoutingRule:
    """Regra de roteamento para contextos específicos"""
    context_type: ContextType
    primary_llm: LLMProvider
    fallback_llms: List[LLMProvider]
    confidence_threshold: float
    max_retries: int = 3

class LLMRouter:
    """Roteador inteligente para múltiplas LLMs"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Detectar caminho dinamicamente
            try:
                from app.config import config
                self.config_path = config.workspace_root.parent / "config" / "llm_config.json"
            except ImportError:
                # Fallback: usar caminho relativo ao arquivo atual
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent.parent
                self.config_path = project_root / "config" / "llm_config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.llm_configs: Dict[LLMProvider, LLMConfig] = {}
        self.performance_metrics: Dict[LLMProvider, LLMPerformanceMetrics] = {}
        self.routing_rules: Dict[ContextType, RoutingRule] = {}
        
        self._load_configuration()
        self._initialize_default_routing()
    
    def _load_configuration(self):
        """Carrega configuração das LLMs"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._parse_configuration(config_data)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
                self._create_default_configuration()
        else:
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Cria configuração padrão"""
        default_config = {
            "llm_configs": {
                "openai_gpt4": {
                    "provider": "openai_gpt4",
                    "name": "GPT-4",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "api_key": "${OPENAI_API_KEY}",
                    "model_name": "gpt-4",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "cost_per_token": 0.00003,
                    "rate_limit": 60,
                    "timeout": 30,
                    "enabled": True
                },
                "openai_gpt4_turbo": {
                    "provider": "openai_gpt4_turbo",
                    "name": "GPT-4 Turbo",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "api_key": "${OPENAI_API_KEY}",
                    "model_name": "gpt-4-turbo-preview",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "cost_per_token": 0.00001,
                    "rate_limit": 100,
                    "timeout": 30,
                    "enabled": True
                },
                "anthropic_claude_sonnet": {
                    "provider": "anthropic_claude_sonnet",
                    "name": "Claude 3.5 Sonnet",
                    "api_endpoint": "https://api.anthropic.com/v1/messages",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model_name": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "cost_per_token": 0.000015,
                    "rate_limit": 50,
                    "timeout": 30,
                    "enabled": True
                }
            },
            "routing_rules": {
                "code_generation": {
                    "context_type": "code_generation",
                    "primary_llm": "anthropic_claude_sonnet",
                    "fallback_llms": ["openai_gpt4", "openai_gpt4_turbo"],
                    "confidence_threshold": 0.8,
                    "max_retries": 3
                },
                "data_analysis": {
                    "context_type": "data_analysis",
                    "primary_llm": "openai_gpt4",
                    "fallback_llms": ["anthropic_claude_sonnet", "openai_gpt4_turbo"],
                    "confidence_threshold": 0.7,
                    "max_retries": 3
                },
                "creative_writing": {
                    "context_type": "creative_writing",
                    "primary_llm": "anthropic_claude_sonnet",
                    "fallback_llms": ["openai_gpt4_turbo", "openai_gpt4"],
                    "confidence_threshold": 0.9,
                    "max_retries": 2
                },
                "general_chat": {
                    "context_type": "general_chat",
                    "primary_llm": "openai_gpt4_turbo",
                    "fallback_llms": ["anthropic_claude_sonnet", "openai_gpt4"],
                    "confidence_threshold": 0.6,
                    "max_retries": 3
                }
            }
        }
        
        self._save_configuration(default_config)
        self._parse_configuration(default_config)
    
    def _parse_configuration(self, config_data: Dict[str, Any]):
        """Parseia dados de configuração"""
        # Carregar configurações de LLM
        for provider_key, llm_data in config_data.get("llm_configs", {}).items():
            try:
                provider = LLMProvider(provider_key)
                self.llm_configs[provider] = LLMConfig(**llm_data)
            except ValueError:
                logger.warning(f"Provedor LLM desconhecido: {provider_key}")
        
        # Carregar regras de roteamento
        for context_key, rule_data in config_data.get("routing_rules", {}).items():
            try:
                context_type = ContextType(context_key)
                rule_data["context_type"] = context_type
                rule_data["primary_llm"] = LLMProvider(rule_data["primary_llm"])
                rule_data["fallback_llms"] = [LLMProvider(p) for p in rule_data["fallback_llms"]]
                self.routing_rules[context_type] = RoutingRule(**rule_data)
            except ValueError as e:
                logger.warning(f"Erro ao parsear regra de roteamento {context_key}: {e}")
    
    def _save_configuration(self, config_data: Dict[str, Any]):
        """Salva configuração"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def _initialize_default_routing(self):
        """Inicializa métricas padrão de performance"""
        for provider in self.llm_configs.keys():
            if provider not in self.performance_metrics:
                self.performance_metrics[provider] = LLMPerformanceMetrics(
                    provider=provider,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    avg_response_time=0.0,
                    avg_tokens_per_request=0.0,
                    total_cost=0.0,
                    last_used=datetime.now(timezone.utc).isoformat(),
                    uptime_percentage=100.0
                )
    
    def classify_context(self, message: str, conversation_history: List[Dict] = None) -> ContextType:
        """Classifica o contexto da mensagem para roteamento"""
        message_lower = message.lower()
        
        # Palavras-chave para classificação
        code_keywords = ["código", "programar", "função", "class", "def", "import", "script", "debug", "erro", "bug"]
        data_keywords = ["dados", "análise", "gráfico", "estatística", "csv", "excel", "tabela", "relatório"]
        creative_keywords = ["história", "poema", "criativo", "narrativa", "personagem", "roteiro", "ficção"]
        technical_keywords = ["configurar", "instalar", "erro", "problema", "solução", "tutorial", "como fazer"]
        research_keywords = ["pesquisar", "informação", "estudo", "artigo", "referência", "fonte", "bibliografia"]
        
        # Contagem de palavras-chave
        code_score = sum(1 for keyword in code_keywords if keyword in message_lower)
        data_score = sum(1 for keyword in data_keywords if keyword in message_lower)
        creative_score = sum(1 for keyword in creative_keywords if keyword in message_lower)
        technical_score = sum(1 for keyword in technical_keywords if keyword in message_lower)
        research_score = sum(1 for keyword in research_keywords if keyword in message_lower)
        
        # Determinar contexto com maior pontuação
        scores = {
            ContextType.CODE_GENERATION: code_score,
            ContextType.DATA_ANALYSIS: data_score,
            ContextType.CREATIVE_WRITING: creative_score,
            ContextType.TECHNICAL_SUPPORT: technical_score,
            ContextType.RESEARCH: research_score
        }
        
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return ContextType.GENERAL_CHAT
    
    def select_llm(self, context_type: ContextType, workspace_id: str = None) -> Tuple[LLMProvider, float]:
        """Seleciona a melhor LLM para o contexto"""
        # Obter regra de roteamento
        routing_rule = self.routing_rules.get(context_type)
        if not routing_rule:
            # Fallback para chat geral
            routing_rule = self.routing_rules.get(ContextType.GENERAL_CHAT)
        
        if not routing_rule:
            # Fallback final - primeira LLM disponível
            for provider, config in self.llm_configs.items():
                if config.enabled:
                    return provider, 1.0
            raise Exception("Nenhuma LLM disponível")
        
        # Verificar LLM primária
        primary_llm = routing_rule.primary_llm
        if self._is_llm_available(primary_llm):
            confidence = self._calculate_confidence(primary_llm, context_type)
            if confidence >= routing_rule.confidence_threshold:
                return primary_llm, confidence
        
        # Tentar LLMs de fallback
        for fallback_llm in routing_rule.fallback_llms:
            if self._is_llm_available(fallback_llm):
                confidence = self._calculate_confidence(fallback_llm, context_type)
                if confidence >= routing_rule.confidence_threshold * 0.8:  # Threshold reduzido para fallback
                    return fallback_llm, confidence
        
        # Fallback final - melhor LLM disponível
        best_llm = self._get_best_available_llm()
        return best_llm, 0.5
    
    def _is_llm_available(self, provider: LLMProvider) -> bool:
        """Verifica se uma LLM está disponível"""
        config = self.llm_configs.get(provider)
        if not config or not config.enabled:
            return False
        
        metrics = self.performance_metrics.get(provider)
        if not metrics:
            return True
        
        # Verificar uptime
        return metrics.uptime_percentage > 50.0
    
    def _calculate_confidence(self, provider: LLMProvider, context_type: ContextType) -> float:
        """Calcula confiança na LLM para o contexto"""
        metrics = self.performance_metrics.get(provider)
        if not metrics or metrics.total_requests == 0:
            return 0.8  # Confiança padrão para LLMs não testadas
        
        # Fatores de confiança
        success_rate = metrics.successful_requests / metrics.total_requests
        uptime_factor = metrics.uptime_percentage / 100.0
        response_time_factor = max(0.1, 1.0 - (metrics.avg_response_time / 30.0))  # Penalizar tempos > 30s
        
        # Peso baseado no contexto
        context_weights = {
            ContextType.CODE_GENERATION: {
                LLMProvider.ANTHROPIC_CLAUDE_SONNET: 1.2,
                LLMProvider.OPENAI_GPT4: 1.0,
                LLMProvider.OPENAI_GPT4_TURBO: 0.9
            },
            ContextType.DATA_ANALYSIS: {
                LLMProvider.OPENAI_GPT4: 1.2,
                LLMProvider.ANTHROPIC_CLAUDE_SONNET: 1.0,
                LLMProvider.OPENAI_GPT4_TURBO: 1.1
            },
            ContextType.CREATIVE_WRITING: {
                LLMProvider.ANTHROPIC_CLAUDE_SONNET: 1.3,
                LLMProvider.OPENAI_GPT4_TURBO: 1.0,
                LLMProvider.OPENAI_GPT4: 0.9
            }
        }
        
        context_weight = context_weights.get(context_type, {}).get(provider, 1.0)
        
        confidence = (success_rate * 0.4 + uptime_factor * 0.3 + response_time_factor * 0.3) * context_weight
        return min(1.0, confidence)
    
    def _get_best_available_llm(self) -> LLMProvider:
        """Retorna a melhor LLM disponível"""
        best_provider = None
        best_score = 0.0
        
        for provider, config in self.llm_configs.items():
            if not config.enabled:
                continue
            
            metrics = self.performance_metrics.get(provider)
            if not metrics:
                score = 0.8
            else:
                success_rate = metrics.successful_requests / max(metrics.total_requests, 1)
                uptime_factor = metrics.uptime_percentage / 100.0
                score = success_rate * uptime_factor
            
            if score > best_score:
                best_score = score
                best_provider = provider
        
        return best_provider or list(self.llm_configs.keys())[0]
    
    async def call_llm(self, provider: LLMProvider, messages: List[Dict], 
                      workspace_id: str = None, **kwargs) -> Dict[str, Any]:
        """Chama uma LLM específica"""
        config = self.llm_configs.get(provider)
        if not config:
            raise ValueError(f"LLM {provider} não configurada")
        
        start_time = time.time()
        
        try:
            # Preparar requisição baseada no provedor
            if provider.value.startswith("openai"):
                response = await self._call_openai(config, messages, **kwargs)
            elif provider.value.startswith("anthropic"):
                response = await self._call_anthropic(config, messages, **kwargs)
            else:
                raise ValueError(f"Provedor {provider} não implementado")
            
            # Atualizar métricas de sucesso
            response_time = time.time() - start_time
            self._update_metrics(provider, True, response_time, response.get("usage", {}))
            
            return response
            
        except Exception as e:
            # Atualizar métricas de falha
            response_time = time.time() - start_time
            self._update_metrics(provider, False, response_time, {})
            raise e
    
    async def _call_openai(self, config: LLMConfig, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Chama API da OpenAI"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": kwargs.get("stream", False)
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def _call_anthropic(self, config: LLMConfig, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Chama API da Anthropic"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Converter formato de mensagens para Anthropic
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                continue  # System messages são tratadas separadamente na Anthropic
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        payload = {
            "model": config.model_name,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature)
        }
        
        # Adicionar system message se existir
        system_messages = [msg["content"] for msg in messages if msg["role"] == "system"]
        if system_messages:
            payload["system"] = "\n".join(system_messages)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
            async with session.post(config.api_endpoint, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
    
    def _update_metrics(self, provider: LLMProvider, success: bool, response_time: float, usage: Dict[str, Any]):
        """Atualiza métricas de performance"""
        metrics = self.performance_metrics.get(provider)
        if not metrics:
            return
        
        # Atualizar contadores
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Atualizar tempo de resposta médio
        total_time = metrics.avg_response_time * (metrics.total_requests - 1) + response_time
        metrics.avg_response_time = total_time / metrics.total_requests
        
        # Atualizar tokens e custo
        if usage and success:
            tokens = usage.get("total_tokens", 0)
            if tokens > 0:
                total_tokens = metrics.avg_tokens_per_request * (metrics.successful_requests - 1) + tokens
                metrics.avg_tokens_per_request = total_tokens / metrics.successful_requests
                
                config = self.llm_configs.get(provider)
                if config:
                    metrics.total_cost += tokens * config.cost_per_token
        
        # Atualizar uptime
        metrics.uptime_percentage = (metrics.successful_requests / metrics.total_requests) * 100
        metrics.last_used = datetime.now(timezone.utc).isoformat()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance de todas as LLMs"""
        stats = {}
        for provider, metrics in self.performance_metrics.items():
            config = self.llm_configs.get(provider)
            stats[provider.value] = {
                "name": config.name if config else provider.value,
                "enabled": config.enabled if config else False,
                "metrics": asdict(metrics)
            }
        return stats

# Instância global do roteador
llm_router = LLMRouter()

