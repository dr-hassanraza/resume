from pydantic_settings import BaseSettings
from typing import List
import os

class LocalSettings(BaseSettings):
    # Database - Use SQLite for local development
    DATABASE_URL: str = "sqlite:///./resume_optimizer.db"
    
    # Redis - Optional for local development
    REDIS_URL: str = "redis://localhost:6380"
    
    # Security
    SECRET_KEY: str = "local-development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Services - These can be empty for testing UI
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    NEBIUS_API_KEY: str = ""
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3001", "http://127.0.0.1:3001"]
    
    # File uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_PATH: str = "./uploads"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 1000  # More lenient for local dev
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # Subscription tiers
    FREE_TIER_LIMIT: int = 10  # More generous for testing
    PRO_TIER_LIMIT: int = 1000
    
    # Enterprise features
    ENABLE_ANALYTICS: bool = True
    ENABLE_WHITE_LABEL: bool = True
    
    class Config:
        env_file = ".env"

# Use local settings for development
settings = LocalSettings()