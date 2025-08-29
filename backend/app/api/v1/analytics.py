from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User, Resume, Optimization, UsageAnalytics, ChatSession
from app.api.v1.auth import get_current_user

router = APIRouter()

class UserAnalyticsResponse(BaseModel):
    total_resumes: int
    total_optimizations: int
    total_chat_sessions: int
    subscription_tier: str
    optimizations_this_month: int
    optimizations_limit: int
    most_used_optimization: Optional[str]
    average_ats_score: float
    score_improvement: float

class UsageStatsResponse(BaseModel):
    period: str
    total_actions: int
    chat_messages: int
    resume_uploads: int
    optimizations: int
    daily_breakdown: List[Dict[str, Any]]

class ResumeStatsResponse(BaseModel):
    total_resumes: int
    by_industry: Dict[str, int]
    by_experience_level: Dict[str, int]
    average_ats_score: float
    score_distribution: Dict[str, int]

@router.get("/user", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for the current user."""
    
    # Basic counts
    total_resumes = db.query(Resume).filter(Resume.user_id == current_user.id).count()
    
    total_optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id == current_user.id
    ).count()
    
    total_chat_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).count()
    
    # Current month optimizations
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    optimizations_this_month = db.query(Optimization).join(Resume).filter(
        Resume.user_id == current_user.id,
        Optimization.created_at >= current_month
    ).count()
    
    # Optimization limits based on subscription
    limits = {"free": 3, "pro": 1000, "enterprise": float('inf')}
    optimizations_limit = limits.get(current_user.subscription_tier, 3)
    
    # Most used optimization type
    most_used_opt = db.query(
        Optimization.optimization_type,
        func.count(Optimization.id).label('count')
    ).join(Resume).filter(
        Resume.user_id == current_user.id
    ).group_by(Optimization.optimization_type).order_by(desc('count')).first()
    
    most_used_optimization = most_used_opt[0] if most_used_opt else None
    
    # Average ATS score
    avg_score_result = db.query(func.avg(Resume.ats_score)).filter(
        Resume.user_id == current_user.id
    ).scalar()
    average_ats_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Score improvement (before vs after optimizations)
    improvements = db.query(
        Optimization.score_before,
        Optimization.score_after
    ).join(Resume).filter(
        Resume.user_id == current_user.id,
        Optimization.score_before.isnot(None),
        Optimization.score_after.isnot(None)
    ).all()
    
    if improvements:
        total_improvement = sum(opt.score_after - opt.score_before for opt in improvements)
        score_improvement = total_improvement / len(improvements)
    else:
        score_improvement = 0.0
    
    return UserAnalyticsResponse(
        total_resumes=total_resumes,
        total_optimizations=total_optimizations,
        total_chat_sessions=total_chat_sessions,
        subscription_tier=current_user.subscription_tier,
        optimizations_this_month=optimizations_this_month,
        optimizations_limit=optimizations_limit,
        most_used_optimization=most_used_optimization,
        average_ats_score=average_ats_score,
        score_improvement=score_improvement
    )

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a specific timeframe."""
    
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map[timeframe]
    start_date = datetime.now() - timedelta(days=days)
    
    # Total actions
    total_actions = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.timestamp >= start_date
    ).count()
    
    # Breakdown by action type
    chat_messages = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.action_type == 'chat',
        UsageAnalytics.timestamp >= start_date
    ).count()
    
    resume_uploads = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.action_type == 'upload',
        UsageAnalytics.timestamp >= start_date
    ).count()
    
    optimizations = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.action_type == 'optimize',
        UsageAnalytics.timestamp >= start_date
    ).count()
    
    # Daily breakdown
    daily_stats = db.query(
        func.date(UsageAnalytics.timestamp).label('date'),
        func.count(UsageAnalytics.id).label('count')
    ).filter(
        UsageAnalytics.user_id == current_user.id,
        UsageAnalytics.timestamp >= start_date
    ).group_by(func.date(UsageAnalytics.timestamp)).all()
    
    daily_breakdown = [
        {"date": str(stat.date), "count": stat.count}
        for stat in daily_stats
    ]
    
    return UsageStatsResponse(
        period=timeframe,
        total_actions=total_actions,
        chat_messages=chat_messages,
        resume_uploads=resume_uploads,
        optimizations=optimizations,
        daily_breakdown=daily_breakdown
    )

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics data."""
    # Basic counts
    total_resumes = db.query(Resume).filter(Resume.user_id == current_user.id).count()
    total_optimizations = db.query(Optimization).join(Resume).filter(Resume.user_id == current_user.id).count()
    total_chats = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
    
    # Recent activity
    recent_resumes = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(desc(Resume.created_at)).limit(5).all()
    
    return {
        "total_resumes": total_resumes,
        "total_optimizations": total_optimizations,
        "total_chats": total_chats,
        "recent_resumes": [{"id": r.id, "title": r.title, "ats_score": r.ats_score} for r in recent_resumes],
        "subscription_tier": current_user.subscription_tier
    }

@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics overview."""
    return {
        "resumes_count": db.query(Resume).filter(Resume.user_id == current_user.id).count(),
        "optimizations_count": db.query(Optimization).join(Resume).filter(Resume.user_id == current_user.id).count(),
        "chat_sessions_count": db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count(),
        "average_ats_score": 75.0  # Placeholder
    }

@router.get("/resumes", response_model=ResumeStatsResponse)
async def get_resume_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resume statistics for the current user."""
    
    user_resumes = db.query(Resume).filter(Resume.user_id == current_user.id)
    
    total_resumes = user_resumes.count()
    
    # By industry
    industry_stats = db.query(
        Resume.industry,
        func.count(Resume.id).label('count')
    ).filter(
        Resume.user_id == current_user.id,
        Resume.industry.isnot(None)
    ).group_by(Resume.industry).all()
    
    by_industry = {stat.industry: stat.count for stat in industry_stats}
    
    # By experience level
    experience_stats = db.query(
        Resume.experience_level,
        func.count(Resume.id).label('count')
    ).filter(
        Resume.user_id == current_user.id,
        Resume.experience_level.isnot(None)
    ).group_by(Resume.experience_level).all()
    
    by_experience_level = {stat.experience_level: stat.count for stat in experience_stats}
    
    # Average ATS score
    avg_score = db.query(func.avg(Resume.ats_score)).filter(
        Resume.user_id == current_user.id
    ).scalar()
    average_ats_score = float(avg_score) if avg_score else 0.0
    
    # Score distribution (ranges)
    score_ranges = {
        "0-25": 0, "26-50": 0, "51-75": 0, "76-90": 0, "91-100": 0
    }
    
    scores = [resume.ats_score for resume in user_resumes.all() if resume.ats_score]
    for score in scores:
        if score <= 25:
            score_ranges["0-25"] += 1
        elif score <= 50:
            score_ranges["26-50"] += 1
        elif score <= 75:
            score_ranges["51-75"] += 1
        elif score <= 90:
            score_ranges["76-90"] += 1
        else:
            score_ranges["91-100"] += 1
    
    return ResumeStatsResponse(
        total_resumes=total_resumes,
        by_industry=by_industry,
        by_experience_level=by_experience_level,
        average_ats_score=average_ats_score,
        score_distribution=score_ranges
    )

@router.get("/optimizations")
async def get_optimization_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get optimization statistics for the current user."""
    
    # Total optimizations
    total_optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id == current_user.id
    ).count()
    
    # By type
    type_stats = db.query(
        Optimization.optimization_type,
        func.count(Optimization.id).label('count'),
        func.avg(Optimization.score_after - Optimization.score_before).label('avg_improvement')
    ).join(Resume).filter(
        Resume.user_id == current_user.id,
        Optimization.score_before.isnot(None),
        Optimization.score_after.isnot(None)
    ).group_by(Optimization.optimization_type).all()
    
    optimization_types = [
        {
            "type": stat.optimization_type,
            "count": stat.count,
            "average_improvement": float(stat.avg_improvement) if stat.avg_improvement else 0.0
        }
        for stat in type_stats
    ]
    
    # Success rate (optimizations that improved scores)
    successful_optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id == current_user.id,
        Optimization.score_after > Optimization.score_before
    ).count()
    
    success_rate = (successful_optimizations / total_optimizations * 100) if total_optimizations > 0 else 0
    
    # Recent optimizations
    recent_optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(desc(Optimization.created_at)).limit(5).all()
    
    recent = [
        {
            "id": opt.id,
            "type": opt.optimization_type,
            "job_title": opt.job_title,
            "created_at": opt.created_at.isoformat(),
            "score_improvement": (opt.score_after - opt.score_before) if (opt.score_after and opt.score_before) else None
        }
        for opt in recent_optimizations
    ]
    
    return {
        "total_optimizations": total_optimizations,
        "optimization_types": optimization_types,
        "success_rate": success_rate,
        "recent_optimizations": recent
    }

@router.post("/track")
async def track_usage(
    action_type: str,
    resource_used: str = None,
    metadata: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track user action for analytics."""
    
    usage_record = UsageAnalytics(
        user_id=current_user.id,
        action_type=action_type,
        resource_used=resource_used,
        metadata=metadata or {}
    )
    
    db.add(usage_record)
    db.commit()
    
    return {"message": "Usage tracked successfully"}