from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
import asyncio
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, ChatSession, ChatMessage
from app.services.ai_service import AIService
from app.services.chat_manager import ChatManager
from app.api.v1.auth import get_current_user

router = APIRouter()

class EnhancedChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, dict] = {}
        self.ai_service = AIService()
        
    async def connect(self, websocket: WebSocket, session_id: str, user_id: Optional[int] = None):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "user_id": user_id,
            "conversation_history": [],
            "context": {},
            "typing": False,
            "connected_at": datetime.utcnow()
        }
        
        # Send enhanced welcome message
        await self.send_message(session_id, {
            "type": "system",
            "content": {
                "message": "🚀 Welcome to Resume AI Assistant! I'm here to help you create the perfect resume.",
                "suggestions": [
                    "Upload your resume to get started",
                    "Ask me about ATS optimization",
                    "Get industry-specific advice",
                    "Compare with job descriptions"
                ],
                "features": [
                    {"icon": "📄", "title": "Resume Analysis", "description": "AI-powered content analysis"},
                    {"icon": "🎯", "title": "ATS Optimization", "description": "Improve keyword matching"},
                    {"icon": "💼", "title": "Job Matching", "description": "Find compatible positions"},
                    {"icon": "📊", "title": "Performance Tracking", "description": "Monitor your progress"}
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                await self.disconnect(session_id)

    async def broadcast_typing_indicator(self, session_id: str, is_typing: bool):
        await self.send_message(session_id, {
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_enhanced_message(self, session_id: str, message_data: dict, db: Session):
        message_type = message_data.get("type")
        content = message_data.get("content", "")
        
        # Show typing indicator
        await self.broadcast_typing_indicator(session_id, True)
        
        try:
            if message_type == "chat":
                await self.handle_chat_message(session_id, content, db)
            elif message_type == "resume_upload":
                await self.handle_resume_upload(session_id, message_data, db)
            elif message_type == "optimization_request":
                await self.handle_optimization_request(session_id, message_data, db)
            elif message_type == "job_match":
                await self.handle_job_matching(session_id, message_data, db)
            elif message_type == "quick_action":
                await self.handle_quick_action(session_id, message_data, db)
                
        finally:
            # Hide typing indicator
            await self.broadcast_typing_indicator(session_id, False)

    async def handle_chat_message(self, session_id: str, content: str, db: Session):
        # Enhanced chat with context awareness
        context = self.session_data[session_id].get("context", {})
        
        # Generate enhanced response
        response = await self.ai_service.generate_enhanced_response(
            content, context, session_id
        )
        
        # Send structured response
        await self.send_message(session_id, {
            "type": "assistant",
            "content": {
                "message": response["message"],
                "suggestions": response.get("suggestions", []),
                "actions": response.get("actions", []),
                "confidence": response.get("confidence", 0.9)
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_resume_upload(self, session_id: str, message_data: dict, db: Session):
        resume_data = message_data.get("resume_data")
        
        # Show processing status
        await self.send_message(session_id, {
            "type": "processing",
            "content": {
                "message": "🔍 Analyzing your resume...",
                "progress": 0,
                "stages": [
                    "Reading document",
                    "Extracting content", 
                    "AI analysis",
                    "Generating insights"
                ]
            }
        })
        
        # Simulate progress updates
        for i, stage in enumerate(["Reading document", "Extracting content", "AI analysis", "Generating insights"]):
            await asyncio.sleep(0.5)
            progress = (i + 1) * 25
            await self.send_message(session_id, {
                "type": "processing",
                "content": {
                    "message": f"🔍 {stage}...",
                    "progress": progress
                }
            })

        # Perform enhanced analysis
        analysis = await self.ai_service.enhanced_resume_analysis(resume_data)
        
        # Send comprehensive results
        await self.send_message(session_id, {
            "type": "resume_analysis",
            "content": {
                "message": "✅ Resume analysis complete!",
                "analysis": analysis,
                "visualData": {
                    "scoreBreakdown": analysis.get("score_breakdown", {}),
                    "skillsChart": analysis.get("skills_analysis", {}),
                    "recommendations": analysis.get("recommendations", [])
                },
                "nextSteps": [
                    "Review the analysis above",
                    "Ask for specific optimizations",
                    "Upload a job description for matching",
                    "Generate an improved version"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_optimization_request(self, session_id: str, message_data: dict, db: Session):
        optimization_type = message_data.get("optimization_type")
        job_description = message_data.get("job_description", "")
        
        # Show AI working
        await self.send_message(session_id, {
            "type": "processing",
            "content": {
                "message": f"🤖 AI is optimizing for {optimization_type}...",
                "progress": 0
            }
        })
        
        # Generate optimizations
        suggestions = await self.ai_service.generate_enhanced_optimizations(
            session_id, optimization_type, job_description
        )
        
        # Send results with interactive elements
        await self.send_message(session_id, {
            "type": "optimization_result",
            "content": {
                "message": f"🎯 {optimization_type} optimization complete!",
                "optimizations": suggestions["optimizations"],
                "scoreImprovement": suggestions.get("score_improvement", {}),
                "beforeAfter": suggestions.get("before_after", {}),
                "actions": [
                    {"label": "Apply Changes", "action": "apply_optimization"},
                    {"label": "Download Updated Resume", "action": "download_resume"},
                    {"label": "Get More Suggestions", "action": "more_suggestions"}
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_job_matching(self, session_id: str, message_data: dict, db: Session):
        job_description = message_data.get("job_description", "")
        
        # Perform job matching analysis
        await self.send_message(session_id, {
            "type": "processing",
            "content": {
                "message": "🔍 Analyzing job compatibility...",
                "progress": 50
            }
        })
        
        match_result = await self.ai_service.analyze_job_match(session_id, job_description)
        
        await self.send_message(session_id, {
            "type": "job_match_result",
            "content": {
                "message": "💼 Job matching analysis complete!",
                "matchScore": match_result["overall_score"],
                "strengths": match_result["strengths"],
                "gaps": match_result["gaps"],
                "recommendations": match_result["recommendations"],
                "visualData": {
                    "skillsMatch": match_result["skills_match"],
                    "experienceMatch": match_result["experience_match"],
                    "keywordMatch": match_result["keyword_match"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_quick_action(self, session_id: str, message_data: dict, db: Session):
        action = message_data.get("action")
        
        if action == "get_tips":
            tips = await self.ai_service.get_daily_tips()
            await self.send_message(session_id, {
                "type": "tips",
                "content": {
                    "message": "💡 Here are today's resume tips:",
                    "tips": tips
                }
            })
        elif action == "industry_insights":
            industry = message_data.get("industry", "technology")
            insights = await self.ai_service.get_industry_insights(industry, "")
            await self.send_message(session_id, {
                "type": "industry_insights",
                "content": {
                    "message": f"📊 {industry.title()} Industry Insights:",
                    "insights": insights
                }
            })

# Global instance
enhanced_chat_manager = EnhancedChatManager()

@router.websocket("/ws/{session_id}")
async def enhanced_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Enhanced WebSocket endpoint with rich interactions."""
    
    user_id = None
    if token:
        try:
            # Implement token validation here
            user_id = 1  # Placeholder
        except:
            pass
    
    await enhanced_chat_manager.connect(websocket, session_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle message with enhanced processing
            await enhanced_chat_manager.handle_enhanced_message(
                session_id, message_data, db
            )
            
    except WebSocketDisconnect:
        await enhanced_chat_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await enhanced_chat_manager.disconnect(session_id)

@router.get("/sessions/stats")
async def get_session_stats():
    """Get real-time session statistics."""
    return {
        "active_sessions": len(enhanced_chat_manager.active_connections),
        "total_messages": sum(
            len(session_data.get("conversation_history", []))
            for session_data in enhanced_chat_manager.session_data.values()
        )
    }

@router.post("/sessions/{session_id}/context")
async def update_session_context(
    session_id: str,
    context: dict,
    current_user: User = Depends(get_current_user)
):
    """Update session context data."""
    if session_id in enhanced_chat_manager.session_data:
        enhanced_chat_manager.session_data[session_id]["context"].update(context)
        return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Session not found")