#!/usr/bin/env python3
"""
FastAPI server for OUDS - Oráculo UDS web interface.
Provides REST API endpoints for frontend communication.
"""

import asyncio
import json
import os
import uuid
import mimetypes
import subprocess
import base64
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

from app.agent.manus import Manus
from app.logger import logger
from app.schema import Message, Role

# Load environment variables
load_dotenv()


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    status: str = "success"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskStatus(BaseModel):
    id: str
    title: str
    status: str  # "pending", "running", "completed", "failed"
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskProgressUpdate(BaseModel):
    session_id: str
    tasks: List[TaskStatus]
    current_step: int
    total_steps: int
    message: Optional[str] = None


class FileInfo(BaseModel):
    name: str
    size: int
    modified: datetime
    type: str
    path: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FileListResponse(BaseModel):
    files: List[FileInfo]
    total_count: int
    workspace_path: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    saved_path: str


class CommandQueueItem(BaseModel):
    id: str
    message: str
    priority: int
    created_at: datetime
    status: str  # "pending", "processing", "completed", "failed"
    session_id: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CommandQueueResponse(BaseModel):
    queue: List[CommandQueueItem]
    current_processing: Optional[CommandQueueItem]
    total_pending: int


class GitHubConfig(BaseModel):
    token: str
    username: Optional[str] = None
    default_repo: Optional[str] = None


class GitHubRepo(BaseModel):
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    clone_url: str
    html_url: str
    default_branch: str


class GitHubCommitRequest(BaseModel):
    repo_name: str
    branch: str = "main"
    commit_message: str
    files: List[str]  # List of file paths relative to workspace


class GitHubCloneRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    target_dir: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# Global session management with workspace support
class SessionManager:
    def __init__(self):
        # Workspace-based data structures
        self.workspaces: Dict[str, Dict] = {}  # workspace_id -> workspace_data
        self.sessions: Dict[str, Dict[str, Dict]] = {}  # workspace_id -> {session_id -> session_data}
        self.agents: Dict[str, Dict[str, Manus]] = {}  # workspace_id -> {session_id -> agent}
        self.task_progress: Dict[str, Dict[str, List[TaskStatus]]] = {}  # workspace_id -> {session_id -> tasks}
        self.websocket_connections: Dict[str, Dict[str, WebSocket]] = {}  # workspace_id -> {session_id -> websocket}
        self.command_queues: Dict[str, Dict[str, List[CommandQueueItem]]] = {}  # workspace_id -> {session_id -> queue}
        self.processing_commands: Dict[str, Dict[str, Optional[CommandQueueItem]]] = {}  # workspace_id -> {session_id -> command}
        self.github_configs: Dict[str, Dict[str, GitHubConfig]] = {}  # workspace_id -> {session_id -> config}
    
    def ensure_workspace(self, workspace_id: str) -> None:
        """Ensure workspace exists and create directory structure"""
        if workspace_id not in self.workspaces:
            # Create workspace data structure
            self.workspaces[workspace_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "session_count": 0
            }
            self.sessions[workspace_id] = {}
            self.agents[workspace_id] = {}
            self.task_progress[workspace_id] = {}
            self.websocket_connections[workspace_id] = {}
            self.command_queues[workspace_id] = {}
            self.processing_commands[workspace_id] = {}
            self.github_configs[workspace_id] = {}
            
            # Create workspace directory structure
            workspace_dir = f"/tmp/ouds_workspace_{workspace_id}"
            os.makedirs(workspace_dir, exist_ok=True)
            
            logger.info(f"Created new workspace: {workspace_id} at {workspace_dir}")
    
    async def get_or_create_session(self, session_id: Optional[str] = None, workspace_id: str = "default") -> str:
        # Ensure workspace exists
        self.ensure_workspace(workspace_id)
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions[workspace_id]:
            # Create new session within workspace
            agent = await Manus.create()
            self.sessions[workspace_id][session_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 0,
                "workspace_id": workspace_id
            }
            self.agents[workspace_id][session_id] = agent
            self.task_progress[workspace_id][session_id] = []
            self.command_queues[workspace_id][session_id] = []
            self.processing_commands[workspace_id][session_id] = None
            
            # Update workspace stats
            self.workspaces[workspace_id]["session_count"] += 1
            self.workspaces[workspace_id]["last_activity"] = datetime.now()
            
            # Auto-configure GitHub with default token from environment
            github_token = os.getenv("GITHUB_TOKEN", "")
            if github_token:
                default_github_config = GitHubConfig(
                    token=github_token,
                    username=None,
                    default_repo=None
                )
                self.github_configs[workspace_id][session_id] = default_github_config
            
            logger.info(f"Created new session: {session_id} in workspace: {workspace_id}")
        
        # Update session activity
        if session_id in self.sessions[workspace_id]:
            self.sessions[workspace_id][session_id]["last_activity"] = datetime.now()
            self.workspaces[workspace_id]["last_activity"] = datetime.now()
        
        return session_id
    
    async def cleanup_session(self, session_id: str, workspace_id: str = "default"):
        if workspace_id in self.agents and session_id in self.agents[workspace_id]:
            await self.agents[workspace_id][session_id].cleanup()
            del self.agents[workspace_id][session_id]
        if workspace_id in self.sessions and session_id in self.sessions[workspace_id]:
            del self.sessions[workspace_id][session_id]
        if workspace_id in self.task_progress and session_id in self.task_progress[workspace_id]:
            del self.task_progress[workspace_id][session_id]
        if workspace_id in self.websocket_connections and session_id in self.websocket_connections[workspace_id]:
            del self.websocket_connections[workspace_id][session_id]
        logger.info(f"Cleaned up session: {session_id} in workspace: {workspace_id}")
    
    def update_activity(self, session_id: str, workspace_id: str = "default"):
        if workspace_id in self.sessions and session_id in self.sessions[workspace_id]:
            self.sessions[workspace_id][session_id]["last_activity"] = datetime.now()
            self.sessions[workspace_id][session_id]["message_count"] += 1
            self.workspaces[workspace_id]["last_activity"] = datetime.now()
    
    async def update_task_progress(self, session_id: str, tasks: List[TaskStatus], workspace_id: str = "default"):
        """Update task progress and notify connected clients"""
        if workspace_id not in self.task_progress:
            self.task_progress[workspace_id] = {}
        self.task_progress[workspace_id][session_id] = tasks
        
        # Send update via WebSocket if connected
        if workspace_id in self.websocket_connections and session_id in self.websocket_connections[workspace_id]:
            try:
                current_step = len([t for t in tasks if t.status == "completed"])
                total_steps = len(tasks)
                
                update = TaskProgressUpdate(
                    session_id=session_id,
                    tasks=tasks,
                    current_step=current_step,
                    total_steps=total_steps
                )
                
                await self.websocket_connections[workspace_id][session_id].send_text(
                    json.dumps(update.dict(), default=str)
                )
            except Exception as e:
                logger.error(f"Error sending task progress update: {e}")
                # Remove broken connection
                if workspace_id in self.websocket_connections and session_id in self.websocket_connections[workspace_id]:
                    del self.websocket_connections[workspace_id][session_id]
    
    def add_command_to_queue(self, session_id: str, message: str, priority: int = 1, workspace_id: str = "default") -> CommandQueueItem:
        """Add a command to the session's queue."""
        if workspace_id not in self.command_queues:
            self.command_queues[workspace_id] = {}
        if session_id not in self.command_queues[workspace_id]:
            self.command_queues[workspace_id][session_id] = []
            
        command = CommandQueueItem(
            id=str(uuid.uuid4()),
            message=message,
            priority=priority,
            created_at=datetime.now(),
            status="pending",
            session_id=session_id
        )
        
        # Insert based on priority (higher priority first)
        queue = self.command_queues[workspace_id][session_id]
        inserted = False
        for i, item in enumerate(queue):
            if command.priority > item.priority:
                queue.insert(i, command)
                inserted = True
                break
        
        if not inserted:
            queue.append(command)
        
        logger.info(f"Added command to queue for session {session_id} in workspace {workspace_id}: {message[:50]}...")
        return command
    
    def get_next_command(self, session_id: str, workspace_id: str = "default") -> Optional[CommandQueueItem]:
        """Get the next command from the queue."""
        if (workspace_id not in self.command_queues or 
            session_id not in self.command_queues[workspace_id] or 
            not self.command_queues[workspace_id][session_id]):
            return None
        
        command = self.command_queues[workspace_id][session_id].pop(0)
        command.status = "processing"
        self.processing_commands[workspace_id][session_id] = command
        
        return command
    
    def complete_command(self, session_id: str, command_id: str, success: bool = True, workspace_id: str = "default"):
        """Mark a command as completed."""
        if (workspace_id in self.processing_commands and 
            session_id in self.processing_commands[workspace_id]):
            current = self.processing_commands[workspace_id][session_id]
            if current and current.id == command_id:
                current.status = "completed" if success else "failed"
                self.processing_commands[workspace_id][session_id] = None
    
    def get_command_queue_status(self, session_id: str, workspace_id: str = "default") -> CommandQueueResponse:
        """Get the current queue status for a session."""
        queue = []
        if workspace_id in self.command_queues and session_id in self.command_queues[workspace_id]:
            queue = self.command_queues[workspace_id][session_id]
        
        processing = None
        if workspace_id in self.processing_commands and session_id in self.processing_commands[workspace_id]:
            processing = self.processing_commands[workspace_id][session_id]
        
        return CommandQueueResponse(
            queue=queue,
            processing=processing,
            total_pending=len(queue)
        )
    
    def is_processing_command(self, session_id: str, workspace_id: str = "default") -> bool:
        """Check if a command is currently being processed."""
        return (workspace_id in self.processing_commands and 
                session_id in self.processing_commands[workspace_id] and
                self.processing_commands[workspace_id][session_id] is not None)


# Initialize FastAPI app
app = FastAPI(
    title="OUDS - Oráculo UDS API",
    description="REST API for OUDS - Oráculo UDS Agent",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session manager
session_manager = SessionManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)


manager = ConnectionManager()


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "OUDS - Oráculo UDS API Server",
        "version": "1.2.0",
        "description": "Sistema de IA conversacional baseado no OpenManus com suporte a workspaces",
        "endpoints": {
            "chat": "/api/chat",
            "sessions": "/api/sessions",
            "websocket": "/ws/{session_id}",
            "workspace": "/workspace/{workspace_id}"
        }
    }

# Workspace route handler
@app.get("/workspace/{workspace_id}")
async def workspace_handler(workspace_id: str):
    """Handle workspace access - create if not exists, load if exists."""
    # Ensure workspace exists
    session_manager.ensure_workspace(workspace_id)
    
    # Return workspace info
    workspace_info = session_manager.workspaces[workspace_id]
    return {
        "workspace_id": workspace_id,
        "status": "ready",
        "created_at": workspace_info["created_at"].isoformat(),
        "last_activity": workspace_info["last_activity"].isoformat(),
        "session_count": workspace_info["session_count"],
        "message": f"Workspace '{workspace_id}' está pronto para uso"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for processing user messages with queue support."""
    try:
        # Extract workspace from request or use default
        workspace_id = getattr(request, 'workspace_id', 'default')
        
        # Get or create session
        session_id = await session_manager.get_or_create_session(request.session_id, workspace_id)
        
        # Check if a command is currently being processed
        if session_manager.is_processing_command(session_id, workspace_id):
            # Add to queue with normal priority
            command = session_manager.add_command_to_queue(session_id, request.message, priority=1, workspace_id=workspace_id)
            
            return ChatResponse(
                response=f"Comando adicionado à fila. Posição: {len(session_manager.command_queues[workspace_id][session_id])}. Aguarde a conclusão do comando atual.",
                session_id=session_id,
                timestamp=datetime.now(),
                status="queued"
            )
        
        # Process immediately if no command is running
        return await process_chat_command(session_id, request.message)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_chat_command(session_id: str, message: str, workspace_id: str = "default") -> ChatResponse:
    """Process a chat command immediately."""
    try:
        agent = session_manager.agents[workspace_id][session_id]
        
        # Mark as processing
        command = session_manager.add_command_to_queue(session_id, message, priority=999, workspace_id=workspace_id)  # High priority for immediate processing
        current_command = session_manager.get_next_command(session_id, workspace_id)
        
        # Update session activity
        session_manager.update_activity(session_id, workspace_id)
        
        # Process the message with the agent
        logger.info(f"Processing message in session {session_id} workspace {workspace_id}: {message}")
        
        # Add user message to agent memory
        user_message = Message(
            role=Role.USER,
            content=message
        )
        agent.memory.add_message(user_message)
        
        # Run the agent
        await agent.run(message)
        
        # Get the last assistant message from memory
        assistant_messages = [
            msg for msg in agent.memory.messages 
            if msg.role == Role.ASSISTANT
        ]
        
        if assistant_messages:
            response_content = assistant_messages[-1].content
        else:
            response_content = "I processed your request, but didn't generate a specific response."
        
        # Mark command as completed
        if current_command:
            session_manager.complete_command(session_id, current_command.id, success=True, workspace_id=workspace_id)
        
        # Process next command in queue if any
        asyncio.create_task(process_next_command_in_queue(session_id, workspace_id))
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            timestamp=datetime.now(),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        
        # Mark command as failed
        if (workspace_id in session_manager.processing_commands and 
            session_id in session_manager.processing_commands[workspace_id]):
            current = session_manager.processing_commands[workspace_id][session_id]
            if current:
                session_manager.complete_command(session_id, current.id, success=False, workspace_id=workspace_id)
        
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


async def process_next_command_in_queue(session_id: str, workspace_id: str = "default"):
    """Process the next command in the queue for a session."""
    try:
        next_command = session_manager.get_next_command(session_id, workspace_id)
        if next_command:
            logger.info(f"Processing next command from queue: {next_command.message[:50]}...")
            await process_chat_command(session_id, next_command.message, workspace_id)
    except Exception as e:
        logger.error(f"Error processing next command in queue: {e}")


@app.get("/api/sessions/{session_id}/queue", response_model=CommandQueueResponse)
async def get_command_queue(session_id: str):
    """Get the command queue status for a session."""
    await session_manager.get_or_create_session(session_id)
    return session_manager.get_command_queue_status(session_id)


@app.delete("/api/sessions/{session_id}/queue/{command_id}")
async def cancel_command(session_id: str, command_id: str):
    """Cancel a pending command in the queue."""
    try:
        if session_id in session_manager.command_queues:
            queue = session_manager.command_queues[session_id]
            for i, command in enumerate(queue):
                if command.id == command_id:
                    removed_command = queue.pop(i)
                    logger.info(f"Cancelled command: {removed_command.message[:50]}...")
                    return {"message": "Command cancelled successfully"}
        
        raise HTTPException(status_code=404, detail="Command not found")
    except Exception as e:
        logger.error(f"Error cancelling command: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling command: {str(e)}")


@app.get("/api/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List all active sessions."""
    sessions = []
    for session_id, session_data in session_manager.sessions.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            created_at=session_data["created_at"],
            last_activity=session_data["last_activity"],
            message_count=session_data["message_count"]
        ))
    return sessions


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await session_manager.cleanup_session(session_id)
    return {"message": f"Session {session_id} deleted successfully"}


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a specific session."""
    if session_id not in session_manager.agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = session_manager.agents[session_id]
    messages = []
    
    for msg in agent.memory.messages:
        messages.append({
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": getattr(msg, 'timestamp', None)
        })
    
    return {"session_id": session_id, "messages": messages}


@app.post("/chat/stream")
async def chat_stream_endpoint_v2(request: ChatRequest):
    """Streaming chat endpoint with task progress updates."""
    
    async def generate_response():
        try:
            # Get or create session
            session_id = await session_manager.get_or_create_session(request.session_id)
            agent = session_manager.agents[session_id]
            
            # Update session activity
            session_manager.update_activity(session_id)
            
            # Initialize task progress
            initial_tasks = [
                TaskStatus(
                    id="analyze",
                    title="Analisando solicitação",
                    status="running",
                    description="Processando sua mensagem...",
                    started_at=datetime.now()
                ),
                TaskStatus(
                    id="plan",
                    title="Planejando resposta",
                    status="pending",
                    description="Definindo estratégia de resposta"
                ),
                TaskStatus(
                    id="execute",
                    title="Executando ações",
                    status="pending",
                    description="Realizando tarefas necessárias"
                ),
                TaskStatus(
                    id="respond",
                    title="Gerando resposta",
                    status="pending",
                    description="Formulando resposta final"
                )
            ]
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            
            # Send initial progress with proper datetime serialization
            tasks_dict = []
            for task in initial_tasks:
                task_dict = task.dict()
                if task_dict.get('started_at'):
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_dict.append(task_dict)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': tasks_dict})}\n\n"
            
            # Add user message to agent memory
            user_message = Message(role=Role.USER, content=request.message)
            agent.memory.add_message(user_message)
            
            # Update task 1 to completed
            initial_tasks[0].status = "completed"
            initial_tasks[0].completed_at = datetime.now()
            initial_tasks[1].status = "running"
            initial_tasks[1].started_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            # Convert tasks to dict with proper datetime serialization
            tasks_dict = []
            for task in initial_tasks:
                task_dict = task.dict()
                if task_dict.get('started_at'):
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_dict.append(task_dict)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': tasks_dict})}\n\n"
            
            # Run the agent
            await agent.run(request.message)
            
            # Update task 2 to completed
            initial_tasks[1].status = "completed"
            initial_tasks[1].completed_at = datetime.now()
            initial_tasks[2].status = "running"
            initial_tasks[2].started_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            # Convert tasks to dict with proper datetime serialization
            tasks_dict = []
            for task in initial_tasks:
                task_dict = task.dict()
                if task_dict.get('started_at'):
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_dict.append(task_dict)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': tasks_dict})}\n\n"
            
            # Get the response
            assistant_messages = [
                msg for msg in agent.memory.messages 
                if msg.role == Role.ASSISTANT
            ]
            
            if assistant_messages:
                response_content = assistant_messages[-1].content
            else:
                response_content = "Processamento concluído."
            
            # Update task 3 to completed
            initial_tasks[2].status = "completed"
            initial_tasks[2].completed_at = datetime.now()
            initial_tasks[3].status = "running"
            initial_tasks[3].started_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            # Convert tasks to dict with proper datetime serialization
            tasks_dict = []
            for task in initial_tasks:
                task_dict = task.dict()
                if task_dict.get('started_at'):
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_dict.append(task_dict)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': tasks_dict})}\n\n"
            
            # Stream the response word by word
            words = response_content.split()
            current_text = ""
            
            for i, word in enumerate(words):
                current_text += word + " "
                yield f"data: {json.dumps({'type': 'response', 'content': current_text.strip(), 'partial': True})}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Final response
            yield f"data: {json.dumps({'type': 'response', 'content': response_content, 'partial': False})}\n\n"
            
            # Update final task to completed
            initial_tasks[3].status = "completed"
            initial_tasks[3].completed_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            # Convert tasks to dict with proper datetime serialization
            tasks_dict = []
            for task in initial_tasks:
                task_dict = task.dict()
                if task_dict.get('started_at'):
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_dict.append(task_dict)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': tasks_dict})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.get("/api/sessions/{session_id}/progress")
async def get_task_progress(session_id: str):
    """Get current task progress for a session."""
    if session_id not in session_manager.task_progress:
        raise HTTPException(status_code=404, detail="Session not found")
    
    tasks = session_manager.task_progress[session_id]
    current_step = len([t for t in tasks if t.status == "completed"])
    total_steps = len(tasks)
    
    return TaskProgressUpdate(
        session_id=session_id,
        tasks=tasks,
        current_step=current_step,
        total_steps=total_steps
    )


@app.websocket("/ws/progress/{session_id}")
async def websocket_progress_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time task progress updates."""
    await websocket.accept()
    
    # Store connection
    session_manager.websocket_connections[session_id] = websocket
    
    # Ensure session exists
    await session_manager.get_or_create_session(session_id)
    
    try:
        # Send current progress if available
        if session_id in session_manager.task_progress:
            tasks = session_manager.task_progress[session_id]
            current_step = len([t for t in tasks if t.status == "completed"])
            total_steps = len(tasks)
            
            update = TaskProgressUpdate(
                session_id=session_id,
                tasks=tasks,
                current_step=current_step,
                total_steps=total_steps
            )
            
            await websocket.send_text(json.dumps(update.dict(), default=str))
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        if session_id in session_manager.websocket_connections:
            del session_manager.websocket_connections[session_id]
        logger.info(f"Progress WebSocket disconnected for session: {session_id}")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket, session_id)
    
    # Ensure session exists
    await session_manager.get_or_create_session(session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                
                # Process with agent
                agent = session_manager.agents[session_id]
                session_manager.update_activity(session_id)
                
                # Add user message to memory
                user_msg = Message(role=Role.USER, content=user_message)
                agent.memory.add_message(user_msg)
                
                # Send acknowledgment
                await manager.send_message(json.dumps({
                    "type": "status",
                    "message": "Processing your request..."
                }), session_id)
                
                # Run agent
                await agent.run(user_message)
                
                # Get response
                assistant_messages = [
                    msg for msg in agent.memory.messages 
                    if msg.role == Role.ASSISTANT
                ]
                
                if assistant_messages:
                    response_content = assistant_messages[-1].content
                else:
                    response_content = "Request processed."
                
                # Send response
                await manager.send_message(json.dumps({
                    "type": "response",
                    "message": response_content,
                    "timestamp": datetime.now().isoformat()
                }), session_id)
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")


# File management endpoints
@app.get("/api/workspace/files", response_model=FileListResponse)
async def list_workspace_files(workspace_id: str = "default"):
    """List all files in the workspace directory."""
    try:
        # Use workspace-specific directory
        workspace_path = Path(f"/tmp/ouds_workspace_{workspace_id}")
        workspace_path.mkdir(exist_ok=True)
        
        files = []
        for file_path in workspace_path.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append(FileInfo(
                    name=file_path.name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                    path=str(file_path.relative_to(workspace_path))
                ))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.modified, reverse=True)
        
        return FileListResponse(
            files=files,
            total_count=len(files),
            workspace_path=str(workspace_path.absolute())
        )
    
    except Exception as e:
        logger.error(f"Error listing workspace files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.get("/api/workspace/files/{filename}/download")
async def download_workspace_file(filename: str, workspace_id: str = "default"):
    """Download a file from the workspace."""
    try:
        # Use workspace-specific directory
        workspace_path = Path(f"/tmp/ouds_workspace_{workspace_id}")
        file_path = workspace_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(workspace_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        # Determine media type
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.get("/api/workspace/files/{filename}/preview")
async def preview_workspace_file(filename: str, workspace_id: str = "default"):
    """Preview a text file from the workspace."""
    try:
        # Use workspace-specific directory
        workspace_path = Path(f"/tmp/ouds_workspace_{workspace_id}")
        file_path = workspace_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(workspace_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        # Check if file is text-based
        mime_type = mimetypes.guess_type(str(file_path))[0]
        if mime_type and not (mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']):
            raise HTTPException(status_code=400, detail="File is not previewable")
        
        # Read file content (limit to 1MB for safety)
        max_size = 1024 * 1024  # 1MB
        if file_path.stat().st_size > max_size:
            raise HTTPException(status_code=400, detail="File too large for preview")
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with latin-1 encoding
            content = file_path.read_text(encoding='latin-1')
        
        return {"content": content, "filename": filename, "size": file_path.stat().st_size}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")


@app.delete("/api/workspace/files/{filename}")
async def delete_workspace_file(filename: str, workspace_id: str = "default"):
    """Delete a file from the workspace."""
    try:
        # Use workspace-specific directory
        workspace_path = Path(f"/tmp/ouds_workspace_{workspace_id}")
        file_path = workspace_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(workspace_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        file_path.unlink()
        
        return {"message": f"File '{filename}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.post("/api/workspace/files/upload", response_model=UploadResponse)
async def upload_workspace_file(file: UploadFile = File(...), workspace_id: str = "default"):
    """Upload a file to the workspace."""
    try:
        # Use workspace-specific directory
        workspace_path = Path(f"/tmp/ouds_workspace_{workspace_id}")
        workspace_path.mkdir(exist_ok=True)
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Security: sanitize filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-").rstrip()
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check file size (limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Check if file already exists and create unique name if needed
        file_path = workspace_path / safe_filename
        counter = 1
        original_name = safe_filename
        while file_path.exists():
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                safe_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                safe_filename = f"{original_name}_{counter}"
            file_path = workspace_path / safe_filename
            counter += 1
        
        # Write file
        file_path.write_bytes(content)
        
        logger.info(f"File uploaded successfully: {safe_filename} ({len(content)} bytes)")
        
        return UploadResponse(
            message="File uploaded successfully",
            filename=safe_filename,
            size=len(content),
            saved_path=str(file_path.relative_to(workspace_path))
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down OUDS - Oráculo UDS API server...")
    for session_id in list(session_manager.sessions.keys()):
        await session_manager.cleanup_session(session_id)


# GitHub integration endpoints
@app.post("/api/github/config")
async def configure_github(session_id: str, config: GitHubConfig):
    """Configure GitHub token for a session."""
    try:
        # Test the token by making a simple API call
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid GitHub token")
        
        user_data = response.json()
        config.username = user_data.get("login")
        
        # Store configuration
        session_manager.github_configs[session_id] = config
        
        return {
            "message": "GitHub configured successfully",
            "username": config.username
        }
        
    except requests.RequestException as e:
        logger.error(f"Error testing GitHub token: {e}")
        raise HTTPException(status_code=400, detail="Failed to validate GitHub token")


@app.get("/api/github/repos")
async def list_github_repos(session_id: str):
    """List user's GitHub repositories."""
    try:
        if session_id not in session_manager.github_configs:
            raise HTTPException(status_code=400, detail="GitHub not configured for this session")
        
        config = session_manager.github_configs[session_id]
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get("https://api.github.com/user/repos", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch repositories")
        
        repos_data = response.json()
        repos = []
        
        for repo in repos_data:
            repos.append(GitHubRepo(
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                private=repo["private"],
                clone_url=repo["clone_url"],
                html_url=repo["html_url"],
                default_branch=repo["default_branch"]
            ))
        
        return {"repositories": repos}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing GitHub repos: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing repositories: {str(e)}")


@app.post("/api/github/clone")
async def clone_github_repo(session_id: str, request: GitHubCloneRequest):
    """Clone a GitHub repository to the workspace."""
    try:
        if session_id not in session_manager.github_configs:
            raise HTTPException(status_code=400, detail="GitHub not configured for this session")
        
        config = session_manager.github_configs[session_id]
        workspace_path = Path("workspace")
        workspace_path.mkdir(exist_ok=True)
        
        # Determine target directory
        if request.target_dir:
            target_path = workspace_path / request.target_dir
        else:
            repo_name = request.repo_url.split("/")[-1].replace(".git", "")
            target_path = workspace_path / repo_name
        
        # Prepare git clone command with authentication
        auth_url = request.repo_url.replace("https://", f"https://{config.username}:{config.token}@")
        
        cmd = ["git", "clone", auth_url, str(target_path)]
        if request.branch:
            cmd.extend(["-b", request.branch])
        
        # Execute git clone
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=workspace_path)
        
        if result.returncode != 0:
            logger.error(f"Git clone failed: {result.stderr}")
            raise HTTPException(status_code=400, detail=f"Clone failed: {result.stderr}")
        
        return {
            "message": "Repository cloned successfully",
            "target_path": str(target_path.relative_to(workspace_path)),
            "repo_url": request.repo_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        raise HTTPException(status_code=500, detail=f"Error cloning repository: {str(e)}")


@app.post("/api/github/commit")
async def commit_to_github(session_id: str, request: GitHubCommitRequest):
    """Commit files from workspace to GitHub repository."""
    try:
        if session_id not in session_manager.github_configs:
            raise HTTPException(status_code=400, detail="GitHub not configured for this session")
        
        config = session_manager.github_configs[session_id]
        workspace_path = Path("workspace")
        repo_path = workspace_path / request.repo_name
        
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail="Repository not found in workspace")
        
        # Configure git user (required for commits)
        subprocess.run(["git", "config", "user.name", config.username or "Oráculo"], 
                      cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", f"{config.username}@users.noreply.github.com"], 
                      cwd=repo_path, check=True)
        
        # Add specified files
        for file_path in request.files:
            full_path = repo_path / file_path
            if full_path.exists():
                subprocess.run(["git", "add", file_path], cwd=repo_path, check=True)
        
        # Commit changes
        result = subprocess.run(
            ["git", "commit", "-m", request.commit_message],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                return {"message": "No changes to commit"}
            else:
                raise HTTPException(status_code=400, detail=f"Commit failed: {result.stderr}")
        
        # Push to remote
        push_result = subprocess.run(
            ["git", "push", "origin", request.branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            logger.error(f"Git push failed: {push_result.stderr}")
            raise HTTPException(status_code=400, detail=f"Push failed: {push_result.stderr}")
        
        return {
            "message": "Changes committed and pushed successfully",
            "commit_message": request.commit_message,
            "files": request.files
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        raise HTTPException(status_code=400, detail=f"Git operation failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error committing to GitHub: {e}")
        raise HTTPException(status_code=500, detail=f"Error committing: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Configurações via variáveis de ambiente
    host = os.getenv("OUDS_API_HOST", "0.0.0.0")
    port = int(os.getenv("OUDS_API_PORT", "8000"))
    reload = os.getenv("OUDS_API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("OUDS_API_LOG_LEVEL", "info").lower()
    
    print(f"🚀 Iniciando OUDS API Server em {host}:{port}")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )

