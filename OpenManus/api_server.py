#!/usr/bin/env python3
"""
FastAPI server for OUDS - Oráculo UDS web interface.
Provides REST API endpoints for frontend communication.
"""

import asyncio
import json
import os
import uuid
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from app.agent.manus import Manus
from app.logger import logger
from app.schema import Message, Role


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    status: str = "success"


class TaskStatus(BaseModel):
    id: str
    title: str
    status: str  # "pending", "running", "completed", "failed"
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskProgressUpdate(BaseModel):
    session_id: str
    tasks: List[TaskStatus]
    current_step: int
    total_steps: int
    message: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int


# Global session management
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.agents: Dict[str, Manus] = {}
        self.task_progress: Dict[str, List[TaskStatus]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    async def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            # Create new session
            agent = await Manus.create()
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 0
            }
            self.agents[session_id] = agent
            self.task_progress[session_id] = []
            logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    async def cleanup_session(self, session_id: str):
        if session_id in self.agents:
            await self.agents[session_id].cleanup()
            del self.agents[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.task_progress:
            del self.task_progress[session_id]
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
        logger.info(f"Cleaned up session: {session_id}")
    
    def update_activity(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["message_count"] += 1
    
    async def update_task_progress(self, session_id: str, tasks: List[TaskStatus]):
        """Update task progress and notify connected clients"""
        self.task_progress[session_id] = tasks
        
        # Send update via WebSocket if connected
        if session_id in self.websocket_connections:
            try:
                current_step = len([t for t in tasks if t.status == "completed"])
                total_steps = len(tasks)
                
                update = TaskProgressUpdate(
                    session_id=session_id,
                    tasks=tasks,
                    current_step=current_step,
                    total_steps=total_steps
                )
                
                await self.websocket_connections[session_id].send_text(
                    json.dumps(update.dict(), default=str)
                )
            except Exception as e:
                logger.error(f"Error sending task progress update: {e}")
                # Remove broken connection
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]


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
        "version": "1.0.0",
        "description": "Sistema de IA conversacional baseado no OpenManus",
        "endpoints": {
            "chat": "/api/chat",
            "sessions": "/api/sessions",
            "websocket": "/ws/{session_id}"
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for processing user messages."""
    try:
        # Get or create session
        session_id = await session_manager.get_or_create_session(request.session_id)
        agent = session_manager.agents[session_id]
        
        # Update session activity
        session_manager.update_activity(session_id)
        
        # Process the message with the agent
        logger.info(f"Processing message in session {session_id}: {request.message}")
        
        # Add user message to agent memory
        user_message = Message(
            role=Role.USER,
            content=request.message
        )
        agent.memory.add_message(user_message)
        
        # Run the agent
        await agent.run(request.message)
        
        # Get the last assistant message from memory
        assistant_messages = [
            msg for msg in agent.memory.messages 
            if msg.role == Role.ASSISTANT
        ]
        
        if assistant_messages:
            response_content = assistant_messages[-1].content
        else:
            response_content = "I processed your request, but didn't generate a specific response."
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            timestamp=datetime.now(),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


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


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
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
            
            # Send initial progress
            yield f"data: {json.dumps({'type': 'progress', 'tasks': [t.dict() for t in initial_tasks]})}\n\n"
            
            # Add user message to agent memory
            user_message = Message(role=Role.USER, content=request.message)
            agent.memory.add_message(user_message)
            
            # Update task 1 to completed
            initial_tasks[0].status = "completed"
            initial_tasks[0].completed_at = datetime.now()
            initial_tasks[1].status = "running"
            initial_tasks[1].started_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': [t.dict() for t in initial_tasks]})}\n\n"
            
            # Run the agent
            await agent.run(request.message)
            
            # Update task 2 to completed
            initial_tasks[1].status = "completed"
            initial_tasks[1].completed_at = datetime.now()
            initial_tasks[2].status = "running"
            initial_tasks[2].started_at = datetime.now()
            
            await session_manager.update_task_progress(session_id, initial_tasks)
            yield f"data: {json.dumps({'type': 'progress', 'tasks': [t.dict() for t in initial_tasks]})}\n\n"
            
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
            yield f"data: {json.dumps({'type': 'progress', 'tasks': [t.dict() for t in initial_tasks]})}\n\n"
            
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
            yield f"data: {json.dumps({'type': 'progress', 'tasks': [t.dict() for t in initial_tasks]})}\n\n"
            
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
async def websocket_endpoint(websocket: WebSocket, session_id: str)::
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down OUDS - Oráculo UDS API server...")
    for session_id in list(session_manager.sessions.keys()):
        await session_manager.cleanup_session(session_id)


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

