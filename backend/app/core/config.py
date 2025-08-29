from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./resume_optimizer.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Services
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    NEBIUS_API_KEY: str = ""
    Z_AI_API_KEY: str = "" # Added for Z.AI integration
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
    
    # File uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_PATH: str = "./uploads"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # Subscription tiers
    FREE_TIER_LIMIT: int = 3  # optimizations per month
    PRO_TIER_LIMIT: int = 1000
    
    # Enterprise features
    ENABLE_ANALYTICS: bool = True
    ENABLE_WHITE_LABEL: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()