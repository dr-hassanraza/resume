from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    date_of_birth = Column(DateTime)
    profile_picture_url = Column(String)
    bio = Column(Text)
    location = Column(String)
    website = Column(String)
    linkedin_url = Column(String)
    github_url = Column(String)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String)
    password_reset_token = Column(String)
    password_reset_expires = Column(DateTime)
    subscription_tier = Column(String, default="free")  # free, pro, enterprise
    preferences = Column(JSON)  # User preferences and settings
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resumes = relationship("Resume", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    usage_analytics = relationship("UsageAnalytics", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_text = Column(Text)
    content_json = Column(JSON)  # Structured resume data
    ats_score = Column(Float, default=0.0)
    industry = Column(String)
    experience_level = Column(String)  # entry, mid, senior, executive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    optimizations = relationship("Optimization", back_populates="resume")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    status = Column(String, default="active")  # active, completed, abandoned
    context_data = Column(JSON)  # Conversation context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # text, file, optimization
    message_metadata = Column(JSON)  # Additional message data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class Optimization(Base):
    __tablename__ = "optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    optimization_type = Column(String, nullable=False)
    job_title = Column(String)
    job_description = Column(Text)
    suggestions = Column(Text)
    score_before = Column(Float)
    score_after = Column(Float)
    status = Column(String, default="pending")  # pending, applied, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="optimizations")

class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String, nullable=False)  # upload, optimize, chat
    resource_used = Column(String)  # model name, feature used
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    analytics_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="usage_analytics")

class Enterprise(Base):
    __tablename__ = "enterprises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    subscription_plan = Column(String, default="basic")
    api_key = Column(String, unique=True)
    white_label_config = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    industry = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    trending_keywords = Column(JSON)
    salary_range = Column(JSON)
    skill_demand = Column(JSON)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String, unique=True, nullable=False)
    device_info = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String, nullable=False)  # google, linkedin, github
    provider_user_id = Column(String, nullable=False)
    provider_email = Column(String)
    provider_data = Column(JSON)  # Additional data from provider
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String)
    success = Column(Boolean, default=False)
    failure_reason = Column(String)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())