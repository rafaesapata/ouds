#!/usr/bin/env python3
"""
FastAPI server for OUDS - Oráculo UDS web interface.
Provides REST API endpoints for frontend communication.
"""

import asyncio
import json
import os
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
            logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    async def cleanup_session(self, session_id: str):
        if session_id in self.agents:
            await self.agents[session_id].cleanup()
            del self.agents[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
        logger.info(f"Cleaned up session: {session_id}")
    
    def update_activity(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["message_count"] += 1


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

