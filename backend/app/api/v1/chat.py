from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.models import User, ChatSession, ChatMessage
from app.api.v1.auth import get_current_user

router = APIRouter()

class ChatSessionCreate(BaseModel):
    resume_id: Optional[int] = None

class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    status: str
    created_at: datetime
    resume_id: Optional[int]

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    message_type: str
    created_at: datetime

class SendMessageRequest(BaseModel):
    session_id: str
    content: str
    message_type: str = "text"

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    
    db_session = ChatSession(
        session_id=session_id,
        user_id=current_user.id,
        resume_id=session_data.resume_id,
        status="active",
        context_data={}
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all chat sessions for the current user."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return session

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit).all()
    
    return messages

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to a chat session (for REST API usage)."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Save user message
    db_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=message_data.content,
        message_type=message_data.message_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.put("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat session status."""
    if status not in ["active", "completed", "abandoned"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session.status = status
    db.commit()
    
    return {"message": "Status updated successfully"}

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete all messages first
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    
    # Delete session
    db.delete(session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}