from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import json
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Resume Optimizer Chatbot API (Simple Mode)")
    yield
    # Shutdown
    logger.info("Shutting down Resume Optimizer Chatbot API")

app = FastAPI(
    title="Resume Optimizer Chatbot API",
    description="Enterprise-grade resume optimization with conversational AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo
chat_sessions: Dict[str, list] = {}
uploaded_resumes: list = [
    {
        "id": 1,
        "title": "Demo Resume",
        "ats_score": 75.5,
        "industry": "technology",
        "experience_level": "mid",
        "created_at": "2024-01-01T00:00:00Z"
    }
]

@app.get("/")
async def root():
    return {
        "message": "Resume Optimizer Chatbot API (Simple Mode)",
        "version": "1.0.0",
        "status": "running",
        "note": "This is a simplified version for local testing"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "simple"}

@app.post("/api/v1/auth/register")
async def register():
    return {
        "access_token": "demo_token_123",
        "token_type": "bearer",
        "user_id": 1,
        "subscription_tier": "free"
    }

@app.post("/api/v1/auth/login")
async def login():
    return {
        "access_token": "demo_token_123",
        "token_type": "bearer",
        "user_id": 1,
        "subscription_tier": "free"
    }

@app.get("/api/v1/auth/me")
async def get_current_user():
    return {
        "id": 1,
        "email": "demo@example.com",
        "username": "demo_user",
        "full_name": "Demo User",
        "subscription_tier": "free",
        "is_active": True
    }

@app.post("/api/v1/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    title: str = Form(...)
):
    # Simulate resume upload - in demo mode we just return success
    # The file parameter receives the uploaded file but we don't process it in demo mode
    
    logger.info(f"File upload simulation: {file.filename}, title: {title}")
    
    # Create new resume entry and add to our demo list
    new_resume = {
        "id": len(uploaded_resumes) + 1,
        "title": title,
        "ats_score": 78.5,
        "industry": "technology", 
        "experience_level": "mid",
        "created_at": "2024-01-01T00:00:00Z",
        "content_text": f"Demo resume content from file: {file.filename}. In full mode, this would contain the actual resume text extracted from your PDF."
    }
    
    uploaded_resumes.append(new_resume)
    
    return new_resume

@app.get("/api/v1/resumes/")
async def list_resumes():
    return uploaded_resumes

@app.get("/api/v1/analytics/user")
async def get_user_analytics():
    return {
        "total_resumes": 1,
        "total_optimizations": 3,
        "total_chat_sessions": 2,
        "subscription_tier": "free",
        "optimizations_this_month": 3,
        "optimizations_limit": 10,
        "most_used_optimization": "ATS Keyword Optimizer",
        "average_ats_score": 75.5,
        "score_improvement": 5.2
    }

@app.websocket("/api/v1/chat/ws/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat communication."""
    await websocket.accept()
    
    # Initialize session if not exists
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    try:
        logger.info(f"WebSocket connected: session={session_id}")
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "system",
            "message": "Welcome! I'm your AI resume optimization assistant. This is a demo mode - upload functionality is simulated.",
            "timestamp": 1640995200000
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"Received message: {message_data}")
            
            # Store message
            chat_sessions[session_id].append(message_data)
            
            # Generate demo response
            if message_data.get("type") == "chat":
                response_message = generate_demo_response(message_data.get("message", ""))
                await websocket.send_text(json.dumps({
                    "type": "assistant",
                    "message": response_message,
                    "timestamp": 1640995200000
                }))
            
            elif message_data.get("type") == "resume_upload":
                await websocket.send_text(json.dumps({
                    "type": "resume_analysis",
                    "message": "## Resume Analysis Complete\n\n**Strengths:**\n• Strong technical background\n• Clear project descriptions\n• Good use of action verbs\n\n**Areas for Improvement:**\n• Add more quantifiable achievements\n• Include relevant keywords for ATS\n• Improve formatting consistency\n\n**ATS Score:** 75/100",
                    "timestamp": 1640995200000
                }))
            
            elif message_data.get("type") == "optimization_request":
                optimization_type = message_data.get("optimization_type", "General")
                await websocket.send_text(json.dumps({
                    "type": "optimization_result",
                    "message": f"## {optimization_type} Results\n\n**Key Improvements:**\n• Add industry-specific keywords\n• Strengthen experience descriptions\n• Improve formatting for ATS compatibility\n\n**Recommended Actions:**\n• Update skills section with trending technologies\n• Add quantifiable metrics to achievements\n• Optimize for target job requirements",
                    "optimization_type": optimization_type,
                    "timestamp": 1640995200000
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)

def generate_demo_response(user_message: str) -> str:
    """Generate a demo response based on user input."""
    user_message_lower = user_message.lower()
    
    if "upload" in user_message_lower or "resume" in user_message_lower:
        return "I'd be happy to help you optimize your resume! In this demo mode, please use the upload button to simulate uploading a resume, and I'll provide you with detailed analysis and optimization suggestions."
    
    elif "ats" in user_message_lower or "score" in user_message_lower:
        return "ATS (Applicant Tracking System) compatibility is crucial for getting your resume seen by hiring managers. I can help you improve your ATS score by optimizing keywords, formatting, and content structure. What specific area would you like to focus on?"
    
    elif "keyword" in user_message_lower:
        return "Keywords are essential for ATS optimization! I can help you identify relevant keywords for your industry and role. Make sure to include both hard skills (technical abilities) and soft skills (communication, leadership) that match the job description."
    
    elif "help" in user_message_lower or "how" in user_message_lower:
        return "I can help you with:\n\n• **Resume Analysis** - Upload your resume for detailed feedback\n• **ATS Optimization** - Improve compatibility with hiring systems\n• **Keyword Enhancement** - Add relevant industry terms\n• **Content Improvement** - Strengthen experience descriptions\n• **Formatting Tips** - Ensure professional presentation\n\nWhat would you like to work on first?"
    
    else:
        return "That's a great question! I'm here to help you optimize your resume for maximum impact. Whether you need help with ATS compatibility, keyword optimization, or general improvements, I'm ready to assist. What specific aspect of your resume would you like to focus on?"

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )