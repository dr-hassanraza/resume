"""
API Monetization and Rate Limiting System
Handles API key management, rate limiting, and billing
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import redis
import hashlib
import secrets
import json
import logging
from dataclasses import dataclass, asdict

from ..enterprise.subscription_manager import (
    subscription_manager, 
    usage_tracker,
    SubscriptionTier,
    BillingCycle
)

logger = logging.getLogger(__name__)

# Initialize Redis for rate limiting
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class APIKeyType(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

@dataclass
class APIKey:
    key_id: str
    user_id: str
    key_hash: str  # Hashed API key for security
    name: str
    key_type: APIKeyType
    subscription_tier: SubscriptionTier
    rate_limit: int  # Requests per minute
    monthly_quota: int  # Monthly API calls
    permissions: List[str]
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any]

class RateLimitInfo(BaseModel):
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None

class APIUsageStats(BaseModel):
    total_calls: int
    calls_this_month: int
    successful_calls: int
    error_calls: int
    avg_response_time_ms: float
    top_endpoints: List[Dict[str, Any]]
    monthly_quota: int
    quota_remaining: int

# API Models
class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    key_type: APIKeyType = APIKeyType.DEVELOPMENT
    permissions: List[str] = ["read", "write"]
    expires_in_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str  # Only returned on creation
    name: str
    key_type: APIKeyType
    rate_limit: int
    monthly_quota: int
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

class UpdateAPIKeyRequest(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

router = APIRouter(prefix="/api/v1/monetization", tags=["API Monetization"])
security = HTTPBearer()

class APIKeyManager:
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.key_lookup: Dict[str, str] = {}  # hash -> key_id mapping
        
    async def create_api_key(self, user_id: str, request: CreateAPIKeyRequest) -> APIKeyResponse:
        """Create a new API key for user"""
        try:
            # Get user's subscription tier
            user_tier = await self._get_user_subscription_tier(user_id)
            
            # Generate API key
            api_key = self._generate_api_key()
            key_hash = self._hash_api_key(api_key)
            key_id = f"ak_{secrets.token_hex(16)}"
            
            # Set limits based on subscription tier
            rate_limit, monthly_quota = self._get_tier_limits(user_tier, request.key_type)
            
            # Set expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now() + timedelta(days=request.expires_in_days)
            
            # Create API key object
            api_key_obj = APIKey(
                key_id=key_id,
                user_id=user_id,
                key_hash=key_hash,
                name=request.name,
                key_type=request.key_type,
                subscription_tier=user_tier,
                rate_limit=rate_limit,
                monthly_quota=monthly_quota,
                permissions=request.permissions,
                created_at=datetime.now(),
                last_used=None,
                expires_at=expires_at,
                is_active=True,
                metadata={}
            )
            
            # Store API key
            self.api_keys[key_id] = api_key_obj
            self.key_lookup[key_hash] = key_id
            
            logger.info(f"API key created for user {user_id}: {key_id}")
            
            return APIKeyResponse(
                key_id=key_id,
                api_key=api_key,  # Only return on creation
                name=request.name,
                key_type=request.key_type,
                rate_limit=rate_limit,
                monthly_quota=monthly_quota,
                permissions=request.permissions,
                created_at=api_key_obj.created_at,
                expires_at=expires_at
            )
            
        except Exception as e:
            logger.error(f"API key creation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to create API key")

    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        prefix = "roc"  # Resume Optimizer Chatbot
        key_part = secrets.token_hex(32)
        return f"{prefix}_{key_part}"

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def _get_user_subscription_tier(self, user_id: str) -> SubscriptionTier:
        """Get user's subscription tier (mock implementation)"""
        # In production, query from database
        return SubscriptionTier.PROFESSIONAL

    def _get_tier_limits(self, tier: SubscriptionTier, key_type: APIKeyType) -> tuple[int, int]:
        """Get rate limits and quotas based on subscription tier"""
        base_limits = {
            SubscriptionTier.FREE: (60, 1000),  # 60/min, 1k/month
            SubscriptionTier.PROFESSIONAL: (300, 50000),  # 300/min, 50k/month  
            SubscriptionTier.ENTERPRISE: (1000, 500000),  # 1000/min, 500k/month
            SubscriptionTier.ENTERPRISE_PLUS: (5000, -1)  # 5000/min, unlimited
        }
        
        rate_limit, monthly_quota = base_limits[tier]
        
        # Adjust for key type
        if key_type == APIKeyType.ENTERPRISE:
            rate_limit = min(rate_limit * 2, 10000)
        elif key_type == APIKeyType.DEVELOPMENT:
            rate_limit = min(rate_limit // 2, rate_limit)
            
        return rate_limit, monthly_quota

    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate and return API key information"""
        key_hash = self._hash_api_key(api_key)
        
        if key_hash not in self.key_lookup:
            return None
            
        key_id = self.key_lookup[key_hash]
        api_key_obj = self.api_keys.get(key_id)
        
        if not api_key_obj or not api_key_obj.is_active:
            return None
            
        # Check expiration
        if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
            return None
            
        # Update last used
        api_key_obj.last_used = datetime.now()
        
        return api_key_obj

    async def check_rate_limit(self, api_key_obj: APIKey, endpoint: str) -> RateLimitInfo:
        """Check rate limit for API key"""
        key_id = api_key_obj.key_id
        current_minute = datetime.now().strftime("%Y-%m-%d-%H-%M")
        redis_key = f"rate_limit:{key_id}:{current_minute}"
        
        # Get current count
        current_count = redis_client.get(redis_key)
        current_count = int(current_count) if current_count else 0
        
        # Calculate remaining
        remaining = max(0, api_key_obj.rate_limit - current_count)
        
        # Calculate reset time
        reset_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # If over limit, return rate limit info with retry_after
        if current_count >= api_key_obj.rate_limit:
            retry_after = int((reset_time - datetime.now()).total_seconds())
            return RateLimitInfo(
                limit=api_key_obj.rate_limit,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after
            )
        
        # Increment counter
        pipe = redis_client.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, 60)  # Expire after 1 minute
        pipe.execute()
        
        # Track usage
        await usage_tracker.track_api_call(api_key_obj.user_id, endpoint)
        
        return RateLimitInfo(
            limit=api_key_obj.rate_limit,
            remaining=remaining - 1,
            reset_time=reset_time
        )

# Global API key manager
api_key_manager = APIKeyManager()

async def get_api_key_info(credentials: HTTPAuthorizationCredentials = Security(security)) -> APIKey:
    """Dependency to validate API key and get key info"""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
        
    api_key_obj = await api_key_manager.validate_api_key(credentials.credentials)
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    return api_key_obj

async def check_rate_limit_dependency(request: Request, api_key_obj: APIKey = Depends(get_api_key_info)) -> APIKey:
    """Dependency to check rate limits"""
    endpoint = request.url.path
    
    rate_limit_info = await api_key_manager.check_rate_limit(api_key_obj, endpoint)
    
    if rate_limit_info.retry_after:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info.limit),
                "X-RateLimit-Remaining": str(rate_limit_info.remaining),
                "X-RateLimit-Reset": str(int(rate_limit_info.reset_time.timestamp())),
                "Retry-After": str(rate_limit_info.retry_after)
            }
        )
    
    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limit_info.limit),
        "X-RateLimit-Remaining": str(rate_limit_info.remaining),
        "X-RateLimit-Reset": str(int(rate_limit_info.reset_time.timestamp()))
    }
    
    return api_key_obj

# API Routes

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: CreateAPIKeyRequest):
    """Create a new API key"""
    # In production, get user_id from JWT token
    user_id = "user123"  # Mock user ID
    
    return await api_key_manager.create_api_key(user_id, request)

@router.get("/api-keys")
async def list_api_keys():
    """List user's API keys (without the actual key values)"""
    # In production, filter by authenticated user
    user_id = "user123"
    
    user_keys = [
        {
            "key_id": key.key_id,
            "name": key.name,
            "key_type": key.key_type.value,
            "rate_limit": key.rate_limit,
            "monthly_quota": key.monthly_quota,
            "permissions": key.permissions,
            "created_at": key.created_at,
            "last_used": key.last_used,
            "expires_at": key.expires_at,
            "is_active": key.is_active
        }
        for key in api_key_manager.api_keys.values()
        if key.user_id == user_id
    ]
    
    return {"api_keys": user_keys}

@router.put("/api-keys/{key_id}")
async def update_api_key(key_id: str, request: UpdateAPIKeyRequest):
    """Update API key settings"""
    if key_id not in api_key_manager.api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key_obj = api_key_manager.api_keys[key_id]
    
    if request.name:
        api_key_obj.name = request.name
    if request.permissions:
        api_key_obj.permissions = request.permissions
    if request.is_active is not None:
        api_key_obj.is_active = request.is_active
    
    return {"message": "API key updated successfully"}

@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Delete an API key"""
    if key_id not in api_key_manager.api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key_obj = api_key_manager.api_keys[key_id]
    
    # Remove from lookup
    if api_key_obj.key_hash in api_key_manager.key_lookup:
        del api_key_manager.key_lookup[api_key_obj.key_hash]
    
    # Remove API key
    del api_key_manager.api_keys[key_id]
    
    logger.info(f"API key deleted: {key_id}")
    
    return {"message": "API key deleted successfully"}

@router.get("/api-keys/{key_id}/usage", response_model=APIUsageStats)
async def get_api_usage(key_id: str):
    """Get API usage statistics for a key"""
    if key_id not in api_key_manager.api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key_obj = api_key_manager.api_keys[key_id]
    usage_summary = await usage_tracker.get_usage_summary(api_key_obj.user_id)
    
    # Calculate remaining quota
    quota_remaining = api_key_obj.monthly_quota
    if api_key_obj.monthly_quota > 0:
        quota_remaining = max(0, api_key_obj.monthly_quota - usage_summary.get("api_calls", 0))
    
    return APIUsageStats(
        total_calls=usage_summary.get("api_calls", 0),
        calls_this_month=usage_summary.get("api_calls", 0),
        successful_calls=usage_summary.get("api_calls", 0),  # Mock
        error_calls=0,  # Mock
        avg_response_time_ms=245.5,  # Mock
        top_endpoints=[
            {"endpoint": endpoint, "calls": count}
            for endpoint, count in usage_summary.get("endpoints", {}).items()
        ],
        monthly_quota=api_key_obj.monthly_quota,
        quota_remaining=quota_remaining
    )

@router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    plans = subscription_manager.get_all_plans()
    return {
        "plans": [
            {
                "tier": plan.tier.value,
                "name": plan.name,
                "description": plan.description,
                "monthly_price": plan.monthly_price,
                "yearly_price": plan.yearly_price,
                "features": asdict(plan.features),
                "popular": plan.popular,
                "enterprise_only": plan.enterprise_only
            }
            for plan in plans
        ]
    }

@router.post("/subscription/upgrade")
async def upgrade_subscription(tier: SubscriptionTier, billing_cycle: BillingCycle = BillingCycle.MONTHLY):
    """Upgrade user subscription"""
    user_id = "user123"  # Mock user ID
    
    result = await subscription_manager.upgrade_subscription(user_id, tier, billing_cycle)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])

# Webhook endpoint for payment providers
@router.post("/webhooks/payment")
async def handle_payment_webhook(request: Request):
    """Handle payment provider webhooks (Stripe, PayPal, etc.)"""
    # Verify webhook signature
    # Process payment events
    # Update subscription status
    
    body = await request.body()
    
    # Mock webhook processing
    logger.info("Payment webhook received")
    
    return {"status": "processed"}

# Middleware to add rate limit headers to all responses
class RateLimitHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Add rate limit headers if available
                    if hasattr(request.state, "rate_limit_headers"):
                        for key, value in request.state.rate_limit_headers.items():
                            headers[key.encode()] = value.encode()
                            
                        message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)