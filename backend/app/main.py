from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import json
import asyncio
from typing import Dict, List
import logging
from datetime import datetime

try:
    from app.core.config import settings
except ImportError:
    from app.core.config_local import settings
from app.core.database import engine, SessionLocal
from app.api.v1 import auth, resumes, chat, analytics, enterprise
from app.services.chat_manager import ChatManager
from app.services.ai_service import AIService
from app.models import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Resume Optimizer Chatbot API")
    
    # Initialize database tables
    models.Base.metadata.create_all(bind=engine)
    
    # Initialize AI services
    app.state.ai_service = AIService()
    app.state.chat_manager = ChatManager()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Optimizer Chatbot API")

app = FastAPI(
    title="Resume Optimizer Chatbot API",
    description="Enterprise-grade resume optimization with conversational AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Set to False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["Resumes"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(enterprise.router, prefix="/api/v1/enterprise", tags=["Enterprise"])

@app.get("/")
async def root():
    return {
        "message": "Resume Optimizer Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Helper function for WebSocket authentication
from jose import jwt, JWTError
from app.models.models import User
from sqlalchemy.orm import Session

async def get_current_user_from_websocket(websocket: WebSocket, token: str, db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user.id # Return user_id for chat manager

@app.websocket("/api/v1/chat/ws/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str # Token is now required
):
    """WebSocket endpoint for real-time chat communication."""
    await websocket.accept()

    db = SessionLocal() # Get a DB session for this WebSocket connection
    try:
        user_id = await get_current_user_from_websocket(websocket, token, db)
        
        # Register connection
        chat_manager = app.state.chat_manager
        await chat_manager.connect(websocket, session_id, user_id)
        
        logger.info(f"WebSocket connected: session={session_id}, user={user_id}")
        
        # Send welcome message
        await chat_manager.send_message(session_id, {
            "type": "system",
            "message": "Welcome! I'm your AI resume optimization assistant. Upload your resume to get started!",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"Received message: {message_data}")
            
            # Process message based on type
            if message_data.get("type") == "chat":
                await handle_chat_message(session_id, message_data, chat_manager)
            elif message_data.get("type") == "resume_upload":
                await handle_resume_upload(session_id, message_data, chat_manager)
            elif message_data.get("type") == "optimization_request":
                await handle_optimization_request(session_id, message_data, chat_manager)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
        await chat_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)

async def handle_chat_message(session_id: str, message_data: dict, chat_manager: ChatManager):
    """Handle general chat messages."""
    user_message = message_data.get("message", "")

    # Add user message to conversation history
    await chat_manager.add_message(session_id, "user", user_message)

    ai_service = app.state.ai_service
    try:
        # Generate AI response
        response = await ai_service.generate_chat_response(session_id, user_message)

        # Send AI response
        await chat_manager.send_message(session_id, {
            "type": "assistant",
            "message": response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Add AI response to conversation history
        await chat_manager.add_message(session_id, "assistant", response)
    except Exception as e:
        logger.error(f"Error generating chat response for session {session_id}: {e}")
        await chat_manager.send_message(session_id, {
            "type": "error",
            "message": "I'm sorry, I encountered an error while processing your request. Please try again.",
            "timestamp": datetime.utcnow().isoformat()
        })

async def handle_resume_upload(session_id: str, message_data: dict, chat_manager: ChatManager):
    """Handle resume upload notifications."""
    resume_data = message_data.get("resume_data")
    
    if not resume_data or not isinstance(resume_data, dict) or "content" not in resume_data:
        await chat_manager.send_message(session_id, {
            "type": "error",
            "message": "Invalid resume data format. Please ensure it's a dictionary with a 'content' key.",
            "timestamp": datetime.utcnow().isoformat()
        })
        return

    resume_text = resume_data.get("content", "")
    if not isinstance(resume_text, str) or len(resume_text) < 50: # Minimum length check
        await chat_manager.send_message(session_id, {
            "type": "error",
            "message": "Resume content is too short or not valid text. Please upload a complete resume.",
            "timestamp": datetime.utcnow().isoformat()
        })
        return
    
    ai_service = app.state.ai_service
    try:
        # Process resume
        analysis = await ai_service.analyze_resume(resume_data)
        
        # Send analysis result
        await chat_manager.send_message(session_id, {
            "type": "resume_analysis",
            "message": f"Great! I've analyzed your resume. Here's what I found:\n\n{analysis}",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error analyzing resume for session {session_id}: {e}")
        await chat_manager.send_message(session_id, {
            "type": "error",
            "message": "I'm sorry, I encountered an error while analyzing your resume. Please try again.",
            "timestamp": datetime.utcnow().isoformat()
        })

async def handle_optimization_request(session_id: str, message_data: dict, chat_manager: ChatManager):
    """Handle resume optimization requests."""
    optimization_type = message_data.get("optimization_type")
    job_description = message_data.get("job_description", "")
    job_title = message_data.get("job_title", "")

    # Send processing message
    await chat_manager.send_message(session_id, {
        "type": "processing",
        "message": f"Analyzing your resume for {optimization_type}... This may take a moment.",
        "timestamp": datetime.utcnow().isoformat()
    })

    ai_service = app.state.ai_service
    try:
        # Generate optimization suggestions
        suggestions = await ai_service.generate_optimization_suggestions(
            session_id, optimization_type, job_title, job_description
        )

        # Send optimization results
        await chat_manager.send_message(session_id, {
            "type": "optimization_result",
            "message": suggestions,
            "optimization_type": optimization_type,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating optimization suggestions for session {session_id}: {e}")
        await chat_manager.send_message(session_id, {
            "type": "error",
            "message": "I'm sorry, I encountered an error while generating optimization suggestions. Please try again.",
            "timestamp": datetime.utcnow().isoformat()
        })

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )