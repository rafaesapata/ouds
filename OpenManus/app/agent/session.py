"""
OUDS - Session Manager
=====================

Gerenciador de sessões para o sistema OUDS.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.agent.base import BaseAgent
from app.agent.toolcall import ToolCallAgent


class Command(BaseModel):
    """Representa um comando a ser processado pelo agente"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    priority: int = 0  # Maior prioridade = processado primeiro
    timestamp: datetime = Field(default_factory=datetime.now)


class CommandQueueResponse(BaseModel):
    """Resposta para consulta de fila de comandos"""
    session_id: str
    processing: Optional[Command] = None
    queue: List[Command] = []
    queue_size: int = 0


class SessionManager:
    """Gerenciador de sessões e workspaces"""
    
    def __init__(self):
        # Estrutura: workspaces[workspace_id][session_id] = session_info
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        
        # Estrutura: sessions[workspace_id][session_id] = session_info
        self.sessions: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Estrutura: agents[workspace_id][session_id] = agent
        self.agents: Dict[str, Dict[str, BaseAgent]] = {}
        
        # Estrutura: command_queues[workspace_id][session_id] = [command1, command2, ...]
        self.command_queues: Dict[str, Dict[str, List[Command]]] = {}
        
        # Estrutura: processing_commands[workspace_id][session_id] = command
        self.processing_commands: Dict[str, Dict[str, Optional[Command]]] = {}
        
        # Inicializar workspace padrão
        self.ensure_workspace("default")
    
    def ensure_workspace(self, workspace_id: str) -> None:
        """Garante que um workspace existe"""
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "session_count": 0
            }
            
            # Inicializar estruturas para o workspace
            self.sessions[workspace_id] = {}
            self.agents[workspace_id] = {}
            self.command_queues[workspace_id] = {}
            self.processing_commands[workspace_id] = {}
    
    async def get_or_create_session(self, session_id: str, workspace_id: str = "default") -> str:
        """Obtém ou cria uma sessão"""
        # Garantir que o workspace existe
        self.ensure_workspace(workspace_id)
        
        # Verificar se a sessão existe
        if session_id not in self.sessions[workspace_id]:
            # Criar nova sessão
            self.sessions[workspace_id][session_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 0
            }
            
            # Criar agente para a sessão
            agent = ToolCallAgent(name=f"agent_{session_id}")
            
            # Inicializar memória do agente
            from app.agent.memory import Memory
            agent.memory = Memory()
            
            # Armazenar agente
            self.agents[workspace_id][session_id] = agent
            
            # Inicializar fila de comandos
            self.command_queues[workspace_id][session_id] = []
            self.processing_commands[workspace_id][session_id] = None
            
            # Atualizar contador de sessões do workspace
            self.workspaces[workspace_id]["session_count"] = len(self.sessions[workspace_id])
        
        # Atualizar atividade da sessão
        self.update_activity(session_id, workspace_id)
        
        return session_id
    
    def update_activity(self, session_id: str, workspace_id: str = "default") -> None:
        """Atualiza o timestamp de última atividade"""
        now = datetime.now()
        
        # Atualizar atividade da sessão
        if workspace_id in self.sessions and session_id in self.sessions[workspace_id]:
            self.sessions[workspace_id][session_id]["last_activity"] = now
            self.sessions[workspace_id][session_id]["message_count"] += 1
        
        # Atualizar atividade do workspace
        if workspace_id in self.workspaces:
            self.workspaces[workspace_id]["last_activity"] = now
    
    def add_command_to_queue(self, session_id: str, message: str, priority: int = 0, workspace_id: str = "default") -> Command:
        """Adiciona um comando à fila de processamento"""
        # Garantir que o workspace e a sessão existem
        if workspace_id not in self.command_queues or session_id not in self.command_queues[workspace_id]:
            self.command_queues[workspace_id] = {}
            self.command_queues[workspace_id][session_id] = []
        
        # Criar comando
        command = Command(message=message, priority=priority)
        
        # Adicionar à fila
        self.command_queues[workspace_id][session_id].append(command)
        
        # Ordenar fila por prioridade (maior primeiro) e timestamp (mais antigo primeiro)
        self.command_queues[workspace_id][session_id].sort(
            key=lambda cmd: (-cmd.priority, cmd.timestamp)
        )
        
        return command
    
    def get_next_command(self, session_id: str, workspace_id: str = "default") -> Optional[Command]:
        """Obtém o próximo comando da fila e o marca como em processamento"""
        # Verificar se há comandos na fila
        if (workspace_id not in self.command_queues or 
            session_id not in self.command_queues[workspace_id] or
            not self.command_queues[workspace_id][session_id]):
            return None
        
        # Verificar se já há um comando em processamento
        if (workspace_id in self.processing_commands and 
            session_id in self.processing_commands[workspace_id] and
            self.processing_commands[workspace_id][session_id] is not None):
            return self.processing_commands[workspace_id][session_id]
        
        # Obter próximo comando
        command = self.command_queues[workspace_id][session_id].pop(0)
        
        # Marcar como em processamento
        if workspace_id not in self.processing_commands:
            self.processing_commands[workspace_id] = {}
        self.processing_commands[workspace_id][session_id] = command
        
        return command
    
    def is_processing_command(self, session_id: str, workspace_id: str = "default") -> bool:
        """Verifica se há um comando sendo processado"""
        return (workspace_id in self.processing_commands and 
                session_id in self.processing_commands[workspace_id] and
                self.processing_commands[workspace_id][session_id] is not None)
    
    def complete_command(self, session_id: str, command_id: str, success: bool = True, workspace_id: str = "default") -> None:
        """Marca um comando como concluído"""
        # Verificar se há um comando em processamento
        if (workspace_id in self.processing_commands and 
            session_id in self.processing_commands[workspace_id] and
            self.processing_commands[workspace_id][session_id] is not None and
            self.processing_commands[workspace_id][session_id].id == command_id):
            # Limpar comando em processamento
            self.processing_commands[workspace_id][session_id] = None
    
    def get_command_queue_status(self, session_id: str, workspace_id: str = "default") -> CommandQueueResponse:
        """Obtém o status da fila de comandos"""
        # Garantir que o workspace e a sessão existem
        if workspace_id not in self.command_queues:
            self.command_queues[workspace_id] = {}
        if session_id not in self.command_queues[workspace_id]:
            self.command_queues[workspace_id][session_id] = []
        
        # Obter comando em processamento
        processing = None
        if (workspace_id in self.processing_commands and 
            session_id in self.processing_commands[workspace_id]):
            processing = self.processing_commands[workspace_id][session_id]
        
        # Obter fila de comandos
        queue = self.command_queues[workspace_id][session_id]
        
        return CommandQueueResponse(
            session_id=session_id,
            processing=processing,
            queue=queue,
            queue_size=len(queue)
        )

