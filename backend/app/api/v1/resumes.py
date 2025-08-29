from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import shutil
from datetime import datetime
import PyPDF2
import io
from fastapi.responses import FileResponse
from app.resume_generator import ResumeGenerator, ResumeData, PersonalInfo, Experience, Education

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Resume, Optimization
from app.api.v1.auth import get_current_user
from app.services.ai_service import AIService

router = APIRouter()

class ResumeResponse(BaseModel):
    id: int
    title: str
    ats_score: float
    industry: Optional[str]
    experience_level: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class OptimizationResponse(BaseModel):
    id: int
    optimization_type: str
    job_title: Optional[str]
    suggestions: str
    score_before: Optional[float]
    score_after: Optional[float]
    status: str
    created_at: datetime

class OptimizationRequest(BaseModel):
    resume_id: int
    optimization_type: str
    job_title: Optional[str] = None
    job_description: Optional[str] = None

@router.get("/debug")
async def debug_endpoint(current_user: User = Depends(get_current_user)):
    """Debug endpoint to test authentication from frontend."""
    return {"message": "Debug endpoint working", "user_id": current_user.id, "user_email": current_user.email}

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a resume file."""
    
    print(f"DEBUG: Upload request from user {current_user.id} ({current_user.email}) - file: {file.filename}")
    
    # Check file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.UPLOAD_PATH, str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from PDF
        content_text = extract_pdf_text(file_path)
        
        # Analyze resume with AI
        ai_service = AIService()
        analysis = await ai_service.analyze_resume({"content": content_text})
        
        # Detect industry and experience level
        industry = await detect_industry_from_content(content_text)
        experience_level = detect_experience_level(content_text)
        
        # Calculate initial ATS score
        ats_score = 75.0  # Placeholder - would be calculated by AI
        
        # Save to database
        db_resume = Resume(
            user_id=current_user.id,
            title=title,
            file_path=file_path,
            content_text=content_text,
            content_json={"analysis": analysis},
            ats_score=ats_score,
            industry=industry,
            experience_level=experience_level
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return db_resume
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.get("/", response_model=List[ResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all resumes for the current user."""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return resumes

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return resume

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_resume(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate optimization suggestions for a resume."""
    
    # Check if user has reached their optimization limit
    if not check_optimization_limit(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Optimization limit reached for your subscription tier"
        )
    
    # Get resume
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        # Generate optimization suggestions
        ai_service = AIService()
        suggestions = await ai_service.generate_optimization_suggestions(
            session_id=f"opt_{current_user.id}_{resume.id}",
            optimization_type=request.optimization_type,
            job_title=request.job_title or "",
            job_description=request.job_description or "",
            resume_data={"content": resume.content_text}
        )
        
        # Calculate scores
        score_before = resume.ats_score
        score_after = score_before + 5.0  # Placeholder improvement
        
        # Save optimization
        db_optimization = Optimization(
            resume_id=resume.id,
            optimization_type=request.optimization_type,
            job_title=request.job_title,
            job_description=request.job_description,
            suggestions=suggestions,
            score_before=score_before,
            score_after=score_after,
            status="pending"
        )
        db.add(db_optimization)
        db.commit()
        db.refresh(db_optimization)
        
        return db_optimization
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating optimization: {str(e)}")

@router.get("/{resume_id}/optimizations", response_model=List[OptimizationResponse])
async def get_resume_optimizations(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all optimizations for a specific resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    optimizations = db.query(Optimization).filter(
        Optimization.resume_id == resume_id
    ).all()
    
    return optimizations

@router.post("/{resume_id}/score")
async def calculate_ats_score(
    resume_id: int,
    job_description: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate ATS compatibility score against a job description."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        ai_service = AIService()
        score_data = await ai_service.calculate_ats_score(
            resume.content_text,
            job_description
        )
        
        # Update resume score
        resume.ats_score = score_data.get("overall_score", resume.ats_score)
        db.commit()
        
        return score_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")

@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a resume as a PDF."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        # Initialize ResumeGenerator
        generator = ResumeGenerator()

        # Parse existing resume content into structured data
        # Assuming content_json contains the analysis needed for parsing
        # If content_json doesn't have 'sections' or 'contact_info', this might need adjustment
        analysis_data = resume.content_json.get("analysis", {})
        
        # Ensure analysis_data has expected structure for parse_existing_resume
        # This is a simplified assumption; real-world might need more robust handling
        if not analysis_data.get("sections") or not analysis_data.get("contact_info"):
             # Fallback or more detailed parsing if AI analysis is not fully structured
             # For now, we'll use a basic structure if not present
             analysis_data["sections"] = analysis_data.get("sections", {})
             analysis_data["contact_info"] = analysis_data.get("contact_info", {})

        resume_data_obj = generator.parse_existing_resume(resume.content_text, analysis_data)

        # Generate PDF bytes
        pdf_bytes = generator.generate_pdf_resume(resume_data_obj, resume.industry or 'general')

        # Return as FileResponse
        return FileResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            filename=f"{resume.title.replace(' ', '_')}_optimized.pdf",
            headers={"Content-Disposition": f"attachment; filename={resume.title.replace(' ', '_')}_optimized.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

def extract_pdf_text(file_path: str) -> str:
    """Extract text content from PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

async def detect_industry_from_content(content: str) -> str:
    """Detect industry from resume content."""
    # Simple keyword-based detection
    content_lower = content.lower()
    
    if any(word in content_lower for word in ["software", "developer", "programming", "python", "javascript"]):
        return "technology"
    elif any(word in content_lower for word in ["finance", "banking", "investment", "financial"]):
        return "finance"
    elif any(word in content_lower for word in ["marketing", "digital", "social media", "advertising"]):
        return "marketing"
    elif any(word in content_lower for word in ["sales", "account", "revenue", "client"]):
        return "sales"
    elif any(word in content_lower for word in ["healthcare", "medical", "nurse", "clinical"]):
        return "healthcare"
    
    return "general"

def detect_experience_level(content: str) -> str:
    """Detect experience level from resume content."""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ["ceo", "president", "vp", "vice president", "director"]):
        return "executive"
    elif any(word in content_lower for word in ["senior", "lead", "principal", "manager"]):
        return "senior"
    elif any(word in content_lower for word in ["junior", "associate", "entry", "intern"]):
        return "entry"
    else:
        return "mid"

def check_optimization_limit(user: User, db: Session) -> bool:
    """Check if user has reached their optimization limit."""
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    optimizations_count = db.query(Optimization).join(Resume).filter(
        Resume.user_id == user.id,
        Optimization.created_at >= current_month
    ).count()
    
    limits = {
        "free": settings.FREE_TIER_LIMIT,
        "pro": settings.PRO_TIER_LIMIT,
        "enterprise": float('inf')
    }
    
    return optimizations_count < limits.get(user.subscription_tier, 0)

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}

@router.put("/{resume_id}")
async def update_resume(
    resume_id: int,
    title: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a resume's title."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume.title = title
    db.commit()
    db.refresh(resume)
    
    return resume