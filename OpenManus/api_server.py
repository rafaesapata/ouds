"""
OUDS - API Server
================

Servidor API para o sistema OUDS (Oráculo UDS).
"""

import asyncio
import json
import logging
import mimetypes
import os
import shutil
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Import agent module
from app.schema import Message, Role
from app.agent.session import Command, CommandQueueResponse, SessionManager

# Create FastAPI app
app = FastAPI(
    title="OUDS API Server",
    description="API Server for OUDS (Oráculo UDS)",
    version="1.2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API requests and responses
class ChatRequest(BaseModel):
    message: str
    session_id: str
    workspace_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    status: str

class FileInfo(BaseModel):
    name: str
    size: int
    modified: datetime
    type: str
    path: str

class FileListResponse(BaseModel):
    files: List[FileInfo]
    total_count: int
    workspace_path: str

class UploadResponse(BaseModel):
    filename: str
    size: int
    type: str
    path: str

class WorkspaceInfo(BaseModel):
    workspace_id: str
    created_at: datetime
    last_activity: datetime
    session_count: int
    status: str

class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceInfo]
    total_count: int

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    status: str

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    total_count: int
    workspace_id: str

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
        return await process_chat_command(session_id, request.message, workspace_id)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Novo endpoint para streaming de chat
@app.post("/chat/stream")
async def chat_stream_endpoint(request: Request):
    """Streaming chat endpoint for processing user messages with SSE."""
    try:
        # Parse request body
        body = await request.json()
        message = body.get("message", "")
        session_id = body.get("session_id", str(uuid.uuid4()))
        workspace_id = body.get("workspace_id", "default")
        
        # Log request
        logger.info(f"Streaming chat request: session={session_id}, workspace={workspace_id}, message={message[:50]}...")
        
        # Get or create session
        session_id = await session_manager.get_or_create_session(session_id, workspace_id)
        
        # Create streaming response
        return StreamingResponse(
            process_chat_stream(session_id, message, workspace_id),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_chat_stream(session_id: str, message: str, workspace_id: str = "default"):
    """Process a chat message and stream the response."""
    try:
        # Get agent for this session
        if workspace_id not in session_manager.agents or session_id not in session_manager.agents[workspace_id]:
            # Create agent if not exists
            from app.agent.toolcall import ToolCallAgent
            session_manager.agents[workspace_id][session_id] = ToolCallAgent(name=f"agent_{session_id}")
        
        agent = session_manager.agents[workspace_id][session_id]
        
        # Log message
        logger.info(f"Processing streaming message in session {session_id} workspace {workspace_id}: {message}")
        
        # Add user message to agent memory
        user_message = Message(
            role=Role.USER,
            content=message
        )
        agent.memory.add_message(user_message)
        
        # Run the agent
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        
        # Process message with knowledge integration
        from app.knowledge.chat_integration import get_context_for_chat
        
        # Get context from knowledge system
        context = await get_context_for_chat(message, workspace_id)
        if context:
            logger.info(f"Applied context to message: {len(context)} chars")
            # Add context to system message
            agent.system_prompt = f"{agent.system_prompt}\n\nContexto relevante:\n{context}"
        
        # Run agent with streaming
        async for chunk in agent.run_with_streaming():
            if isinstance(chunk, str) and chunk.strip():
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            elif isinstance(chunk, dict):
                yield f"data: {json.dumps({'type': 'status', 'data': chunk})}\n\n"
        
        # Send completion message
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {e}")
        error_message = str(e)
        yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"


async def process_chat_command(session_id: str, message: str, workspace_id: str = "default") -> ChatResponse:
    """Process a chat command with knowledge system integration."""
    try:
        # Log do workspace sendo usado
        logger.info(f"Using workspace: {workspace_id}")
        
        # Get agent for this session
        if workspace_id not in session_manager.agents or session_id not in session_manager.agents[workspace_id]:
            # Create agent if not exists
            from app.agent.toolcall import ToolCallAgent
            session_manager.agents[workspace_id][session_id] = ToolCallAgent(name=f"agent_{session_id}")
        
        agent = session_manager.agents[workspace_id][session_id]
        
        logger.info(f"Processing message in session {session_id} workspace {workspace_id}: {message}")
        
        # Add user message to agent memory
        user_message = Message(
            role=Role.USER,
            content=message
        )
        agent.memory.add_message(user_message)
        
        # Run the agent
        from app.knowledge.chat_integration import get_context_for_chat
        
        # Get context from knowledge system
        context = await get_context_for_chat(message, workspace_id)
        if context:
            logger.info(f"Applied context to message: {len(context)} chars")
            # Add context to system message
            agent.system_prompt = f"{agent.system_prompt}\n\nContexto relevante:\n{context}"
        
        response = await agent.run()
        
        # Update activity
        session_manager.update_activity(session_id, workspace_id)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            timestamp=datetime.now(),
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat command: {e}")
        return ChatResponse(
            response=f"Erro ao processar comando: {str(e)}",
            session_id=session_id,
            timestamp=datetime.now(),
            status="error"
        )


@app.get("/api/sessions")
async def list_sessions(workspace_id: str = "default"):
    """List all sessions in a workspace."""
    try:
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get sessions for this workspace
        sessions = []
        for session_id, session_info in session_manager.sessions.get(workspace_id, {}).items():
            sessions.append(SessionInfo(
                session_id=session_id,
                created_at=session_info["created_at"],
                last_activity=session_info["last_activity"],
                message_count=session_info["message_count"],
                status="active"
            ))
        
        return SessionListResponse(
            sessions=sessions,
            total_count=len(sessions),
            workspace_id=workspace_id
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, workspace_id: str = "default"):
    """Delete a session."""
    try:
        # Check if session exists
        if workspace_id not in session_manager.sessions or session_id not in session_manager.sessions[workspace_id]:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found in workspace {workspace_id}")
        
        # Delete session
        del session_manager.sessions[workspace_id][session_id]
        if workspace_id in session_manager.agents and session_id in session_manager.agents[workspace_id]:
            del session_manager.agents[workspace_id][session_id]
        if workspace_id in session_manager.command_queues and session_id in session_manager.command_queues[workspace_id]:
            del session_manager.command_queues[workspace_id][session_id]
        if workspace_id in session_manager.processing_commands and session_id in session_manager.processing_commands[workspace_id]:
            del session_manager.processing_commands[workspace_id][session_id]
        
        # Update session count
        session_manager.workspaces[workspace_id]["session_count"] = len(session_manager.sessions[workspace_id])
        
        return {"message": f"Session {session_id} deleted from workspace {workspace_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.get("/api/sessions/{session_id}/queue")
async def get_session_queue(session_id: str, workspace_id: str = "default"):
    """Get the command queue for a session."""
    try:
        # Check if session exists
        if workspace_id not in session_manager.sessions or session_id not in session_manager.sessions[workspace_id]:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found in workspace {workspace_id}")
        
        # Get queue status
        queue_status = session_manager.get_command_queue_status(session_id, workspace_id)
        
        return queue_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session queue: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session queue: {str(e)}")


@app.get("/api/workspace/files")
async def list_workspace_files(session_id: Optional[str] = None):
    """List files in the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get workspace path
        workspace_path = Path(f"workspace/{workspace_id}/files")
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # List files
        files = []
        for file_path in workspace_path.glob("*"):
            if file_path.is_file():
                files.append(FileInfo(
                    name=file_path.name,
                    size=file_path.stat().st_size,
                    modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                    type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                    path=str(file_path)
                ))
        
        return FileListResponse(
            files=files,
            total_count=len(files),
            workspace_path=str(workspace_path)
        )
        
    except Exception as e:
        logger.error(f"Error listing workspace files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing workspace files: {str(e)}")


@app.get("/api/workspace/files/{filename}/download")
async def download_workspace_file(filename: str, session_id: Optional[str] = None):
    """Download a file from the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get file path
        file_path = Path(f"workspace/{workspace_id}/files/{filename}")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found in workspace {workspace_id}")
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.get("/api/workspace/files/{filename}/preview")
async def preview_workspace_file(filename: str, session_id: Optional[str] = None):
    """Preview a text file from the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get file path
        file_path = Path(f"workspace/{workspace_id}/files/{filename}")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found in workspace {workspace_id}")
        
        # Check if file is text
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if not media_type.startswith("text/") and media_type != "application/json":
            raise HTTPException(status_code=400, detail=f"File {filename} is not a text file")
        
        # Read file content
        content = file_path.read_text(encoding="utf-8")
        
        # Return content
        return {"filename": filename, "content": content, "media_type": media_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")


@app.delete("/api/workspace/files/{filename}")
async def delete_workspace_file(filename: str, session_id: Optional[str] = None):
    """Delete a file from the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get file path
        file_path = Path(f"workspace/{workspace_id}/files/{filename}")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found in workspace {workspace_id}")
        
        # Delete file
        file_path.unlink()
        
        return {"message": f"File {filename} deleted from workspace {workspace_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.post("/api/workspace/files/upload")
async def upload_workspace_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    """Upload a file to the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        for ws_id, sessions in session_manager.sessions.items():
            if session_id in sessions:
                workspace_id = ws_id
                break
        
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        # Get workspace path
        workspace_path = Path(f"workspace/{workspace_id}/files")
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = workspace_path / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        return UploadResponse(
            filename=file.filename,
            size=file_path.stat().st_size,
            type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
            path=str(file_path)
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(session_id)


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

