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
from app.agent import Message, Role
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


async def process_chat_command(session_id: str, message: str, workspace_id: str = "default") -> ChatResponse:
    """Process a chat command with knowledge system integration."""
    try:
        # Log do workspace sendo usado
        logger.info(f"Processando chat para sessão {session_id} no workspace {workspace_id}")
        
        # Try to use knowledge-enhanced chat
        try:
            from app.knowledge.chat_integration import process_chat_with_knowledge
            result = await process_chat_with_knowledge(session_id, message, workspace_id)
            
            return ChatResponse(
                response=result["response"],
                session_id=result["session_id"],
                timestamp=result["timestamp"],
                status=result["status"]
            )
            
        except ImportError:
            logger.warning("Sistema de conhecimento não disponível, usando processamento tradicional")
        except Exception as e:
            logger.error(f"Erro no sistema de conhecimento: {e}, usando fallback")
        
        # Fallback to traditional processing
        agent = session_manager.agents[workspace_id][session_id]
        
        # Mark as processing
        command = session_manager.add_command_to_queue(session_id, message, priority=999, workspace_id=workspace_id)
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
    # Get workspace_id from request headers or default
    workspace_id = "default"  # TODO: Extract from request context
    await session_manager.get_or_create_session(session_id, workspace_id)
    return session_manager.get_command_queue_status(session_id, workspace_id)


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


@app.get("/api/sessions")
async def list_sessions(workspace_id: str = "default"):
    """List all sessions in a workspace."""
    try:
        # Ensure workspace exists
        session_manager.ensure_workspace(workspace_id)
        
        sessions = []
        for session_id in session_manager.sessions.get(workspace_id, {}):
            session_info = session_manager.sessions[workspace_id][session_id]
            sessions.append(SessionInfo(
                session_id=session_id,
                created_at=session_info["created_at"],
                last_activity=session_info["last_activity"],
                message_count=session_info["message_count"],
                status="active"
            ))
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x.last_activity, reverse=True)
        
        return SessionListResponse(
            sessions=sessions,
            total_count=len(sessions),
            workspace_id=workspace_id
        )
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@app.get("/api/workspaces")
async def list_workspaces():
    """List all workspaces."""
    try:
        workspaces = []
        for workspace_id, workspace_info in session_manager.workspaces.items():
            workspaces.append(WorkspaceInfo(
                workspace_id=workspace_id,
                created_at=workspace_info["created_at"],
                last_activity=workspace_info["last_activity"],
                session_count=workspace_info["session_count"],
                status="active"
            ))
        
        # Sort by last activity (most recent first)
        workspaces.sort(key=lambda x: x.last_activity, reverse=True)
        
        return WorkspaceListResponse(
            workspaces=workspaces,
            total_count=len(workspaces)
        )
    
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing workspaces: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, workspace_id: str = "default"):
    """Delete a session."""
    try:
        # Check if session exists
        if workspace_id not in session_manager.sessions or session_id not in session_manager.sessions[workspace_id]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session
        del session_manager.sessions[workspace_id][session_id]
        
        # Delete agent if exists
        if workspace_id in session_manager.agents and session_id in session_manager.agents[workspace_id]:
            del session_manager.agents[workspace_id][session_id]
        
        # Delete command queue if exists
        if workspace_id in session_manager.command_queues and session_id in session_manager.command_queues[workspace_id]:
            del session_manager.command_queues[workspace_id][session_id]
        
        # Delete processing command if exists
        if workspace_id in session_manager.processing_commands and session_id in session_manager.processing_commands[workspace_id]:
            del session_manager.processing_commands[workspace_id][session_id]
        
        # Update workspace session count
        session_manager.workspaces[workspace_id]["session_count"] = len(session_manager.sessions[workspace_id])
        
        return {"message": f"Session {session_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.delete("/api/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Delete a workspace."""
    try:
        # Check if workspace exists
        if workspace_id not in session_manager.workspaces:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Cannot delete default workspace
        if workspace_id == "default":
            raise HTTPException(status_code=403, detail="Cannot delete default workspace")
        
        # Delete workspace
        del session_manager.workspaces[workspace_id]
        
        # Delete sessions
        if workspace_id in session_manager.sessions:
            del session_manager.sessions[workspace_id]
        
        # Delete agents
        if workspace_id in session_manager.agents:
            del session_manager.agents[workspace_id]
        
        # Delete command queues
        if workspace_id in session_manager.command_queues:
            del session_manager.command_queues[workspace_id]
        
        # Delete processing commands
        if workspace_id in session_manager.processing_commands:
            del session_manager.processing_commands[workspace_id]
        
        # Delete workspace directory
        workspace_path = get_workspace_path(workspace_id)
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        
        return {"message": f"Workspace {workspace_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting workspace: {str(e)}")


def get_workspace_path(workspace_id: str) -> Path:
    """Get the path to a workspace directory."""
    # Use workspace-specific directory
    workspace_path = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace", workspace_id))
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create files directory if it doesn't exist
    files_path = workspace_path / "files"
    files_path.mkdir(exist_ok=True)
    
    return workspace_path

@app.get("/api/workspace/files", response_model=FileListResponse)
async def list_workspace_files(session_id: Optional[str] = None):
    """List all files in the workspace directory for the current session."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Use workspace-specific directory
        workspace_path = get_workspace_path(workspace_id)
        files_path = workspace_path / "files"
        files_path.mkdir(exist_ok=True)
        
        files = []
        for file_path in files_path.rglob("*"):
            if file_path.is_file():
                # Skip hidden files and system files
                if file_path.name.startswith('.'):
                    continue
                    
                stat = file_path.stat()
                files.append(FileInfo(
                    name=file_path.name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                    path=str(file_path.relative_to(files_path))
                ))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.modified, reverse=True)
        
        return FileListResponse(
            files=files,
            total_count=len(files),
            workspace_path=str(files_path.absolute())
        )
    
    except Exception as e:
        logger.error(f"Error listing workspace files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

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
                    
        # Use workspace-specific directory
        workspace_path = get_workspace_path(workspace_id)
        files_path = workspace_path / "files"
        file_path = files_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(files_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: file outside workspace")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Determine media type
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
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
                    
        # Use workspace-specific directory
        workspace_path = get_workspace_path(workspace_id)
        files_path = workspace_path / "files"
        file_path = files_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(files_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: file outside workspace")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Determine media type
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        
        # For text files, return content
        if media_type.startswith('text/') or media_type == 'application/json':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return {
                "filename": filename,
                "content": content,
                "type": media_type,
                "size": file_path.stat().st_size
            }
        
        # For images, return base64 encoded content
        elif media_type.startswith('image/'):
            return FileResponse(
                path=str(file_path),
                media_type=media_type,
                filename=filename
            )
        
        # For other files, return metadata only
        else:
            return {
                "filename": filename,
                "content": None,
                "type": media_type,
                "size": file_path.stat().st_size,
                "message": "Preview not available for this file type"
            }
    
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
                    
        # Use workspace-specific directory
        workspace_path = get_workspace_path(workspace_id)
        files_path = workspace_path / "files"
        file_path = files_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(files_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: file outside workspace")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Delete file
        file_path.unlink()
        
        return {"message": f"File {filename} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.post("/api/workspace/files/upload", response_model=UploadResponse)
async def upload_workspace_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload a file to the workspace."""
    try:
        # Get workspace_id from session or use default
        workspace_id = "default"
        if session_id:
            # Find workspace_id for this session
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
                    
        # Use workspace-specific directory
        workspace_path = get_workspace_path(workspace_id)
        files_path = workspace_path / "files"
        files_path.mkdir(exist_ok=True)
        
        # Generate safe filename
        filename = file.filename
        file_path = files_path / filename
        
        # Security check: ensure file is within workspace
        if not str(file_path.resolve()).startswith(str(files_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: file outside workspace")
        
        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Get file info
        stat = file_path.stat()
        
        return UploadResponse(
            filename=filename,
            size=stat.st_size,
            type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
            path=str(file_path.relative_to(files_path))
        )
    
    except HTTPException:
        raise
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
            # Process message
            try:
                message_data = json.loads(data)
                if "message" in message_data:
                    # Get workspace_id from message or use default
                    workspace_id = message_data.get("workspace_id", "default")
                    
                    # Process chat command
                    response = await process_chat_command(session_id, message_data["message"], workspace_id)
                    
                    # Send response
                    await websocket.send_json({
                        "response": response.response,
                        "timestamp": response.timestamp.isoformat(),
                        "status": response.status
                    })
                else:
                    await websocket.send_json({"error": "Invalid message format"})
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({"error": f"Error processing message: {str(e)}"})
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

