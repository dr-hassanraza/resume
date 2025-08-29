from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import secrets
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Enterprise, UsageAnalytics, Resume, Optimization
from app.api.v1.auth import get_current_user

router = APIRouter()

class EnterpriseConfigResponse(BaseModel):
    name: str
    domain: str
    subscription_plan: str
    is_active: bool
    white_label_config: Dict[str, Any]
    api_key_preview: str

class EnterpriseConfigUpdate(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[str] = None
    white_label_config: Optional[Dict[str, Any]] = None

class APIKeyResponse(BaseModel):
    api_key: str
    created_at: datetime

class EnterpriseMetricsResponse(BaseModel):
    total_users: int
    active_users: int
    total_resumes: int
    total_optimizations: int
    api_calls_count: int
    usage_by_day: List[Dict[str, Any]]
    top_optimization_types: List[Dict[str, Any]]

def check_enterprise_access(current_user: User = Depends(get_current_user)):
    """Check if user has enterprise access."""
    if current_user.subscription_tier != "enterprise":
        raise HTTPException(
            status_code=403,
            detail="Enterprise subscription required"
        )
    return current_user

@router.get("/config", response_model=EnterpriseConfigResponse)
async def get_enterprise_config(
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Get enterprise configuration."""
    
    # Find enterprise by user email domain
    user_domain = current_user.email.split('@')[1]
    enterprise = db.query(Enterprise).filter(Enterprise.domain == user_domain).first()
    
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise configuration not found")
    
    return EnterpriseConfigResponse(
        name=enterprise.name,
        domain=enterprise.domain,
        subscription_plan=enterprise.subscription_plan,
        is_active=enterprise.is_active,
        white_label_config=enterprise.white_label_config or {},
        api_key_preview=f"{enterprise.api_key[:8]}..." if enterprise.api_key else "Not generated"
    )

@router.put("/config", response_model=EnterpriseConfigResponse)
async def update_enterprise_config(
    config_update: EnterpriseConfigUpdate,
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Update enterprise configuration."""
    
    user_domain = current_user.email.split('@')[1]
    enterprise = db.query(Enterprise).filter(Enterprise.domain == user_domain).first()
    
    if not enterprise:
        # Create new enterprise configuration
        enterprise = Enterprise(
            name=config_update.name or user_domain,
            domain=user_domain,
            subscription_plan=config_update.subscription_plan or "basic",
            white_label_config=config_update.white_label_config or {},
            api_key=secrets.token_urlsafe(32)
        )
        db.add(enterprise)
    else:
        # Update existing configuration
        if config_update.name:
            enterprise.name = config_update.name
        if config_update.subscription_plan:
            enterprise.subscription_plan = config_update.subscription_plan
        if config_update.white_label_config is not None:
            enterprise.white_label_config = config_update.white_label_config
    
    db.commit()
    db.refresh(enterprise)
    
    return EnterpriseConfigResponse(
        name=enterprise.name,
        domain=enterprise.domain,
        subscription_plan=enterprise.subscription_plan,
        is_active=enterprise.is_active,
        white_label_config=enterprise.white_label_config or {},
        api_key_preview=f"{enterprise.api_key[:8]}..." if enterprise.api_key else "Not generated"
    )

@router.get("/api-key", response_model=APIKeyResponse)
async def get_api_key(
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Get enterprise API key."""
    
    user_domain = current_user.email.split('@')[1]
    enterprise = db.query(Enterprise).filter(Enterprise.domain == user_domain).first()
    
    if not enterprise or not enterprise.api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyResponse(
        api_key=enterprise.api_key,
        created_at=enterprise.created_at
    )

@router.post("/api-key/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Regenerate enterprise API key."""
    
    user_domain = current_user.email.split('@')[1]
    enterprise = db.query(Enterprise).filter(Enterprise.domain == user_domain).first()
    
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise configuration not found")
    
    # Generate new API key
    enterprise.api_key = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(enterprise)
    
    return APIKeyResponse(
        api_key=enterprise.api_key,
        created_at=datetime.now()
    )

@router.get("/metrics", response_model=EnterpriseMetricsResponse)
async def get_enterprise_metrics(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Get enterprise-wide metrics."""
    
    user_domain = current_user.email.split('@')[1]
    
    # Get all users from the same domain
    domain_users = db.query(User).filter(
        User.email.like(f"%@{user_domain}")
    ).all()
    
    user_ids = [user.id for user in domain_users]
    
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map[timeframe]
    start_date = datetime.now() - timedelta(days=days)
    
    # Total and active users
    total_users = len(domain_users)
    active_users = db.query(User).filter(
        User.email.like(f"%@{user_domain}"),
        User.id.in_(
            db.query(UsageAnalytics.user_id).filter(
                UsageAnalytics.timestamp >= start_date
            ).distinct()
        )
    ).count()
    
    # Total resumes and optimizations
    total_resumes = db.query(Resume).filter(Resume.user_id.in_(user_ids)).count()
    
    total_optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id.in_(user_ids)
    ).count()
    
    # API calls count (usage analytics)
    api_calls_count = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id.in_(user_ids),
        UsageAnalytics.timestamp >= start_date
    ).count()
    
    # Usage by day
    daily_usage = db.query(
        func.date(UsageAnalytics.timestamp).label('date'),
        func.count(UsageAnalytics.id).label('count')
    ).filter(
        UsageAnalytics.user_id.in_(user_ids),
        UsageAnalytics.timestamp >= start_date
    ).group_by(func.date(UsageAnalytics.timestamp)).all()
    
    usage_by_day = [
        {"date": str(usage.date), "count": usage.count}
        for usage in daily_usage
    ]
    
    # Top optimization types
    optimization_stats = db.query(
        Optimization.optimization_type,
        func.count(Optimization.id).label('count')
    ).join(Resume).filter(
        Resume.user_id.in_(user_ids),
        Optimization.created_at >= start_date
    ).group_by(Optimization.optimization_type).order_by(desc('count')).limit(5).all()
    
    top_optimization_types = [
        {"type": stat.optimization_type, "count": stat.count}
        for stat in optimization_stats
    ]
    
    return EnterpriseMetricsResponse(
        total_users=total_users,
        active_users=active_users,
        total_resumes=total_resumes,
        total_optimizations=total_optimizations,
        api_calls_count=api_calls_count,
        usage_by_day=usage_by_day,
        top_optimization_types=top_optimization_types
    )

@router.get("/export")
async def export_enterprise_data(
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Export enterprise data."""
    
    user_domain = current_user.email.split('@')[1]
    
    # Get all users from the same domain
    domain_users = db.query(User).filter(
        User.email.like(f"%@{user_domain}")
    ).all()
    
    user_ids = [user.id for user in domain_users]
    
    # Export data
    export_data = {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "subscription_tier": user.subscription_tier,
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active
            }
            for user in domain_users
        ],
        "resumes": [],
        "optimizations": [],
        "usage_analytics": []
    }
    
    # Get resumes
    resumes = db.query(Resume).filter(Resume.user_id.in_(user_ids)).all()
    export_data["resumes"] = [
        {
            "id": resume.id,
            "user_id": resume.user_id,
            "title": resume.title,
            "industry": resume.industry,
            "experience_level": resume.experience_level,
            "ats_score": resume.ats_score,
            "created_at": resume.created_at.isoformat()
        }
        for resume in resumes
    ]
    
    # Get optimizations
    optimizations = db.query(Optimization).join(Resume).filter(
        Resume.user_id.in_(user_ids)
    ).all()
    export_data["optimizations"] = [
        {
            "id": opt.id,
            "resume_id": opt.resume_id,
            "optimization_type": opt.optimization_type,
            "job_title": opt.job_title,
            "score_before": opt.score_before,
            "score_after": opt.score_after,
            "status": opt.status,
            "created_at": opt.created_at.isoformat()
        }
        for opt in optimizations
    ]
    
    # Get usage analytics (last 90 days)
    recent_date = datetime.now() - timedelta(days=90)
    usage_analytics = db.query(UsageAnalytics).filter(
        UsageAnalytics.user_id.in_(user_ids),
        UsageAnalytics.timestamp >= recent_date
    ).all()
    export_data["usage_analytics"] = [
        {
            "id": usage.id,
            "user_id": usage.user_id,
            "action_type": usage.action_type,
            "resource_used": usage.resource_used,
            "timestamp": usage.timestamp.isoformat(),
            "metadata": usage.metadata
        }
        for usage in usage_analytics
    ]
    
    if format == "json":
        return export_data
    else:
        # Convert to CSV format (simplified)
        import io
        import csv
        
        output = io.StringIO()
        
        # Write users CSV
        writer = csv.writer(output)
        writer.writerow(["Type", "Data"])
        writer.writerow(["Export Date", datetime.now().isoformat()])
        writer.writerow(["Domain", user_domain])
        writer.writerow(["Total Users", len(export_data["users"])])
        writer.writerow(["Total Resumes", len(export_data["resumes"])])
        writer.writerow(["Total Optimizations", len(export_data["optimizations"])])
        
        csv_content = output.getvalue()
        output.close()
        
        return {"format": "csv", "content": csv_content}

@router.get("/users")
async def list_enterprise_users(
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """List all users in the enterprise."""
    
    user_domain = current_user.email.split('@')[1]
    
    users = db.query(User).filter(
        User.email.like(f"%@{user_domain}")
    ).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "subscription_tier": user.subscription_tier,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.put("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: int,
    tier: str,
    current_user: User = Depends(check_enterprise_access),
    db: Session = Depends(get_db)
):
    """Update subscription tier for enterprise user."""
    
    if tier not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    user_domain = current_user.email.split('@')[1]
    
    # Check if target user is in the same domain
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or not target_user.email.endswith(f"@{user_domain}"):
        raise HTTPException(status_code=404, detail="User not found in your organization")
    
    target_user.subscription_tier = tier
    db.commit()
    
    return {"message": f"User subscription updated to {tier}"}