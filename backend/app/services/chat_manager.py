from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import asyncio
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, dict] = {}
        self.redis_client = None
        
    async def get_redis(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: Optional[str] = None):
        """Connect a new WebSocket client."""
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "user_id": user_id,
            "conversation_history": [],
            "resume_data": None,
            "context": {}
        }
        
        # Load conversation history from Redis
        await self.load_conversation_history(session_id)
        
        logger.info(f"Client connected: {session_id}")
    
    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket client."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # Save conversation history to Redis before disconnecting
        await self.save_conversation_history(session_id)
        
        if session_id in self.session_data:
            del self.session_data[session_id]
        
        logger.info(f"Client disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                await self.disconnect(session_id)
    
    async def broadcast_message(self, message: dict, exclude_session: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        for session_id, websocket in self.active_connections.items():
            if session_id != exclude_session:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {session_id}: {e}")
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """Add a message to the conversation history."""
        if session_id not in self.session_data:
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
            "metadata": metadata or {}
        }
        
        self.session_data[session_id]["conversation_history"].append(message)
        
        # Keep only last 50 messages to manage memory
        if len(self.session_data[session_id]["conversation_history"]) > 50:
            self.session_data[session_id]["conversation_history"] = \
                self.session_data[session_id]["conversation_history"][-50:]
    
    async def get_conversation_history(self, session_id: str) -> List[dict]:
        """Get conversation history for a session."""
        if session_id in self.session_data:
            return self.session_data[session_id]["conversation_history"]
        return []
    
    async def update_context(self, session_id: str, key: str, value: any):
        """Update session context."""
        if session_id in self.session_data:
            self.session_data[session_id]["context"][key] = value
    
    async def get_context(self, session_id: str, key: str = None):
        """Get session context."""
        if session_id not in self.session_data:
            return None
        
        if key:
            return self.session_data[session_id]["context"].get(key)
        return self.session_data[session_id]["context"]
    
    async def set_resume_data(self, session_id: str, resume_data: dict):
        """Set resume data for a session."""
        if session_id in self.session_data:
            self.session_data[session_id]["resume_data"] = resume_data
            await self.update_context(session_id, "has_resume", True)
    
    async def get_resume_data(self, session_id: str) -> Optional[dict]:
        """Get resume data for a session."""
        if session_id in self.session_data:
            return self.session_data[session_id]["resume_data"]
        return None
    
    async def save_conversation_history(self, session_id: str):
        """Save conversation history to Redis."""
        try:
            redis_client = await self.get_redis()
            if session_id in self.session_data:
                conversation_data = {
                    "conversation_history": self.session_data[session_id]["conversation_history"],
                    "context": self.session_data[session_id]["context"],
                    "resume_data": self.session_data[session_id]["resume_data"]
                }
                await redis_client.setex(
                    f"chat_session:{session_id}",
                    3600 * 24,  # 24 hours
                    json.dumps(conversation_data, default=str)
                )
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    async def load_conversation_history(self, session_id: str):
        """Load conversation history from Redis."""
        try:
            redis_client = await self.get_redis()
            data = await redis_client.get(f"chat_session:{session_id}")
            if data:
                conversation_data = json.loads(data)
                if session_id in self.session_data:
                    self.session_data[session_id].update(conversation_data)
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_connections.keys())
    
    async def get_session_stats(self) -> dict:
        """Get statistics about active sessions."""
        return {
            "active_connections": len(self.active_connections),
            "total_sessions": len(self.session_data),
            "sessions_with_resumes": len([
                s for s in self.session_data.values() 
                if s.get("resume_data") is not None
            ])
        }