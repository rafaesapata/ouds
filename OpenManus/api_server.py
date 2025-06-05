"""
OUDS - API Server
================

Servidor API para o sistema OUDS.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.websockets import WebSocket, WebSocketDisconnect

# Import config
from app.settings import settings

# Import agent module
from app.schema import Message, Role
from app.agent.session import Command, CommandQueueResponse, SessionManager

# Import logger
from app.logger import logger

# Create FastAPI app
app = FastAPI(
    title="OUDS API",
    description="API para o sistema OUDS",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create session manager
session_manager = SessionManager()


# Models
class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    session_id: Optional[str] = None
    workspace_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Chat response model"""

    message: str
    session_id: str
    workspace_id: str = "default"
    timestamp: datetime = Field(default_factory=datetime.now)


class CommandRequest(BaseModel):
    """Command request model"""

    message: str
    priority: int = 0


class SessionResponse(BaseModel):
    """Session response model"""

    session_id: str
    workspace_id: str = "default"
    created_at: datetime
    last_activity: datetime
    message_count: int = 0


class WorkspaceResponse(BaseModel):
    """Workspace response model"""

    workspace_id: str
    created_at: datetime
    last_activity: datetime
    session_count: int = 0


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "OUDS API is running"}


@app.get("/workspace/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace info"""
    # Ensure workspace exists
    session_manager.ensure_workspace(workspace_id)
    
    # Get workspace info
    workspace = session_manager.workspaces[workspace_id]
    
    # Return workspace info
    return WorkspaceResponse(
        workspace_id=workspace_id,
        created_at=workspace["created_at"],
        last_activity=workspace["last_activity"],
        session_count=workspace["session_count"]
    )


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for processing user messages"""
    try:
        # Process chat command
        response = await process_chat_command(
            session_id=request.session_id or str(uuid.uuid4()),
            message=request.message,
            workspace_id=request.workspace_id or "default"
        )
        
        # Return response
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/chat/stream")
async def chat_stream_endpoint(request: Request):
    """Streaming chat endpoint for processing user messages with SSE"""
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
        if workspace_id not in session_manager.agents:
            session_manager.agents[workspace_id] = {}
            
        if session_id not in session_manager.agents[workspace_id]:
            # Create agent if not exists
            from app.agent.toolcall import ToolCallAgent
            session_manager.agents[workspace_id][session_id] = ToolCallAgent(name=f"agent_{session_id}")
        
        agent = session_manager.agents[workspace_id][session_id]
        
        # Log message
        logger.info(f"Processing streaming message in session {session_id} workspace {workspace_id}: {message}")
        
        # Add user message to agent memory
        from app.schema import Message, Role
        user_message = Message(
            role=Role.USER,
            content=message
        )
        
        # Ensure memory is initialized
        if not hasattr(agent, 'memory') or agent.memory is None:
            from app.agent.memory import Memory
            agent.memory = Memory()
            
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
        logger.error(f"Error in streaming chat: {e}", exc_info=True)
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
        from app.schema import Message, Role
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
        
        # Run agent
        response_text = await agent.run()
        
        # Update session info
        if workspace_id in session_manager.sessions and session_id in session_manager.sessions[workspace_id]:
            session_manager.sessions[workspace_id][session_id]["message_count"] += 1
        
        # Return response
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            workspace_id=workspace_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat command: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/sessions")
async def list_sessions():
    """List all sessions"""
    try:
        # Get all sessions
        all_sessions = []
        for workspace_id, sessions in session_manager.sessions.items():
            for session_id, session in sessions.items():
                all_sessions.append(
                    SessionResponse(
                        session_id=session_id,
                        workspace_id=workspace_id,
                        created_at=session["created_at"],
                        last_activity=session["last_activity"],
                        message_count=session["message_count"]
                    )
                )
        
        # Return sessions
        return all_sessions
        
    except Exception as e:
        logger.error(f"Error in list_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session info"""
    try:
        # Find session
        for workspace_id, sessions in session_manager.sessions.items():
            if session_id in sessions:
                session = sessions[session_id]
                return SessionResponse(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    created_at=session["created_at"],
                    last_activity=session["last_activity"],
                    message_count=session["message_count"]
                )
        
        # Session not found
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/sessions/{session_id}/queue")
async def queue_command(session_id: str, command: CommandRequest):
    """Queue a command for processing"""
    try:
        # Find session
        for workspace_id, sessions in session_manager.sessions.items():
            if session_id in sessions:
                # Create command
                cmd = Command(
                    message=command.message,
                    priority=command.priority
                )
                
                # Add command to queue
                if session_id not in session_manager.command_queues[workspace_id]:
                    session_manager.command_queues[workspace_id][session_id] = []
                
                session_manager.command_queues[workspace_id][session_id].append(cmd)
                
                # Sort queue by priority
                session_manager.command_queues[workspace_id][session_id].sort(
                    key=lambda x: x.priority, reverse=True
                )
                
                # Return queue status
                return CommandQueueResponse(
                    session_id=session_id,
                    processing=session_manager.processing_commands[workspace_id].get(session_id),
                    queue=session_manager.command_queues[workspace_id][session_id],
                    queue_size=len(session_manager.command_queues[workspace_id][session_id])
                )
        
        # Session not found
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in queue_command: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/workspace/files")
async def list_workspace_files(session_id: Optional[str] = None):
    """List files in workspace"""
    try:
        # Get workspace ID from session
        workspace_id = "default"
        if session_id:
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Get workspace directory
        workspace_dir = Path(settings.workspace_dir) / workspace_id / "files"
        
        # Create directory if not exists
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # List files
        files = []
        for file_path in workspace_dir.glob("*"):
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": file_path.suffix[1:] if file_path.suffix else "unknown"
                })
        
        # Return files
        return {"files": files, "workspace_id": workspace_id}
        
    except Exception as e:
        logger.error(f"Error in list_workspace_files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/workspace/files/{filename}/download")
async def download_workspace_file(filename: str, session_id: Optional[str] = None):
    """Download file from workspace"""
    try:
        # Get workspace ID from session
        workspace_id = "default"
        if session_id:
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Get file path
        file_path = Path(settings.workspace_dir) / workspace_id / "files" / filename
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_workspace_file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/workspace/files/{filename}/preview")
async def preview_workspace_file(filename: str, session_id: Optional[str] = None):
    """Preview file from workspace"""
    try:
        # Get workspace ID from session
        workspace_id = "default"
        if session_id:
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Get file path
        file_path = Path(settings.workspace_dir) / workspace_id / "files" / filename
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Return file with appropriate content type
        content_type = "application/octet-stream"
        
        # Determine content type based on file extension
        if filename.lower().endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename.lower().endswith(".png"):
            content_type = "image/png"
        elif filename.lower().endswith(".gif"):
            content_type = "image/gif"
        elif filename.lower().endswith(".svg"):
            content_type = "image/svg+xml"
        elif filename.lower().endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.lower().endswith((".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json")):
            content_type = "text/plain"
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preview_workspace_file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/api/workspace/files/{filename}")
async def delete_workspace_file(filename: str, session_id: Optional[str] = None):
    """Delete file from workspace"""
    try:
        # Get workspace ID from session
        workspace_id = "default"
        if session_id:
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Get file path
        file_path = Path(settings.workspace_dir) / workspace_id / "files" / filename
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Delete file
        file_path.unlink()
        
        # Return success
        return {"message": f"File {filename} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_workspace_file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/workspace/files/upload")
async def upload_workspace_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload file to workspace"""
    try:
        # Get workspace ID from session
        workspace_id = "default"
        if session_id:
            for ws_id, sessions in session_manager.sessions.items():
                if session_id in sessions:
                    workspace_id = ws_id
                    break
        
        # Get workspace directory
        workspace_dir = Path(settings.workspace_dir) / workspace_id / "files"
        
        # Create directory if not exists
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = workspace_dir / file.filename
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Return success
        return {
            "message": f"File {file.filename} uploaded",
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "workspace_id": workspace_id
        }
        
    except Exception as e:
        logger.error(f"Error in upload_workspace_file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    try:
        # Get or create session
        workspace_id = "default"  # Default workspace
        session_id = await session_manager.get_or_create_session(session_id, workspace_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to session {session_id}"
        })
        
        # Process messages
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Parse message
            try:
                message = json.loads(data)
                
                # Process message
                if message.get("type") == "chat":
                    # Process chat message
                    response = await process_chat_command(
                        session_id=session_id,
                        message=message.get("message", ""),
                        workspace_id=workspace_id
                    )
                    
                    # Send response
                    await websocket.send_json({
                        "type": "chat",
                        "message": response.message,
                        "session_id": response.session_id,
                        "workspace_id": response.workspace_id,
                        "timestamp": response.timestamp.isoformat()
                    })
                
                elif message.get("type") == "command":
                    # Process command
                    cmd = Command(
                        message=message.get("message", ""),
                        priority=message.get("priority", 0)
                    )
                    
                    # Add command to queue
                    if session_id not in session_manager.command_queues[workspace_id]:
                        session_manager.command_queues[workspace_id][session_id] = []
                    
                    session_manager.command_queues[workspace_id][session_id].append(cmd)
                    
                    # Sort queue by priority
                    session_manager.command_queues[workspace_id][session_id].sort(
                        key=lambda x: x.priority, reverse=True
                    )
                    
                    # Send queue status
                    await websocket.send_json({
                        "type": "queue",
                        "session_id": session_id,
                        "processing": session_manager.processing_commands[workspace_id].get(session_id),
                        "queue": session_manager.command_queues[workspace_id][session_id],
                        "queue_size": len(session_manager.command_queues[workspace_id][session_id])
                    })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}"
                    })
                
            except json.JSONDecodeError:
                # Invalid JSON
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            
            except Exception as e:
                # Error processing message
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        logger.info(f"WebSocket client disconnected: {session_id}")
    
    except Exception as e:
        # Error in WebSocket connection
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=f"Internal server error: {str(e)}")


# Mount static files
# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )

