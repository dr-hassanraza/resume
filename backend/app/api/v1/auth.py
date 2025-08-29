from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, UserSession, EmailVerification, LoginAttempt, SocialAccount

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    confirm_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    subscription_tier: str
    expires_in: int

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    phone_number: Optional[str]
    profile_picture_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    subscription_tier: str
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    password: str
    confirm_password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserSessionResponse(BaseModel):
    id: int
    device_info: Optional[str]
    ip_address: Optional[str]
    is_active: bool
    created_at: datetime
    last_accessed: datetime

def verify_password(plain_password, hashed_password):
    """Verifies a plaintext password against a hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error but do not allow plaintext bypass
        print(f"Password verification error: {e}")
        return False # Always return False on error or mismatch

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_verification_token():
    return secrets.token_urlsafe(32)

def send_verification_email(email: str, token: str, background_tasks: BackgroundTasks):
    """Send email verification email"""
    background_tasks.add_task(_send_email, email, "Email Verification", 
                            f"Please verify your email by clicking: http://localhost:3002/verify-email?token={token}")

def send_password_reset_email(email: str, token: str, background_tasks: BackgroundTasks):
    """Send password reset email"""
    background_tasks.add_task(_send_email, email, "Password Reset", 
                            f"Reset your password by clicking: http://localhost:3002/reset-password?token={token}")

def _send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP (simplified for demo)"""
    try:
        # In production, configure proper SMTP settings
        print(f"Sending email to {to_email}: {subject} - {body}")
        # For demo purposes, we'll just log the email
        # In production, configure with real SMTP server
    except Exception as e:
        print(f"Failed to send email: {e}")

def log_login_attempt(email: str, ip_address: str, user_agent: str, success: bool, 
                     failure_reason: Optional[str], db: Session):
    """Log login attempt for security monitoring"""
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )
    db.add(attempt)
    db.commit()

def create_user_session(user_id: int, request: Request, db: Session):
    """Create a new user session"""
    session_token = secrets.token_urlsafe(32)
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(session)
    db.commit()
    return session_token

def check_rate_limiting(email: str, db: Session) -> bool:
    """Check if user has exceeded login attempt limits"""
    recent_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.attempted_at > datetime.utcnow() - timedelta(hours=1),
        LoginAttempt.success == False
    ).count()
    
    return recent_attempts < 5  # Allow 5 failed attempts per hour

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
async def register(
    user: UserCreate, 
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    # Generate email verification token
    verification_token = generate_verification_token()
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        subscription_tier="free",
        email_verification_token=verification_token,
        preferences={"notifications": True, "theme": "light", "language": "en"}
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    send_verification_email(user.email, verification_token, background_tasks)
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=30)
    
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(db_user.id)}, expires_delta=refresh_token_expires
    )
    
    # Create user session
    create_user_session(db_user.id, request, db)
    
    # Log registration
    log_login_attempt(user.email, request.client.host, 
                     request.headers.get("user-agent", ""), True, None, db)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "subscription_tier": db_user.subscription_tier,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin, 
    request: Request,
    db: Session = Depends(get_db)
):
    # Check rate limiting
    if not check_rate_limiting(user_login.email, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )
    
    user = db.query(User).filter(User.email == user_login.email).first()
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    if not user:
        # Log failed attempt
        log_login_attempt(user_login.email, ip_address, user_agent, 
                         False, "User not found", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_login.password, user.hashed_password):
        # Log failed attempt
        log_login_attempt(user_login.email, ip_address, user_agent, 
                         False, "Invalid password", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # Log failed attempt
        log_login_attempt(user_login.email, ip_address, user_agent, 
                         False, "Account deactivated", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Update user login info
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=30 if user_login.remember_me else 7)
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    # Create user session
    create_user_session(user.id, request, db)
    
    # Log successful login
    log_login_attempt(user_login.email, ip_address, user_agent, True, None, db)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "subscription_tier": user.subscription_tier,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/upgrade", response_model=UserResponse)
async def upgrade_subscription(
    tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if tier not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    current_user.subscription_tier = tier
    db.commit()
    db.refresh(current_user)
    
    return current_user

# Email Verification Endpoints
@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with verification token"""
    user = db.query(User).filter(User.email_verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )
    
    user.email_verified = True
    user.email_verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend email verification"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    verification_token = generate_verification_token()
    user.email_verification_token = verification_token
    db.commit()
    
    send_verification_email(email, verification_token, background_tasks)
    
    return {"message": "Verification email sent"}

# Password Reset Endpoints
@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    user = db.query(User).filter(User.email == password_reset.email).first()
    
    if user:  # Always return success to prevent email enumeration
        reset_token = generate_verification_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        send_password_reset_email(password_reset.email, reset_token, background_tasks)
    
    return {"message": "Password reset email sent if account exists"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    user.hashed_password = get_password_hash(reset_data.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

# Profile Management Endpoints
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

# Session Management Endpoints
@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).all()
    
    return sessions

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    db.commit()
    
    return {"message": "Session revoked"}

@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke all user sessions"""
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "All sessions revoked"}

# Account Management Endpoints
@router.post("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account"""
    current_user.is_active = False
    db.commit()
    
    return {"message": "Account deactivated"}

@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise JWTError()
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=30)
    
    new_access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "subscription_tier": user.subscription_tier,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke session"""
    session_token = request.headers.get("session-token")
    
    if session_token:
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.user_id == current_user.id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
    
    return {"message": "Logged out successfully"}

# Social Login Endpoints
import httpx
from fastapi.responses import RedirectResponse

# Google OAuth2 Settings
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"

@router.get("/google")
async def google_login():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile"
    )

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    token_data = token_response.json()
    id_token = token_data.get("id_token")
    
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
    user_info = user_info_response.json()
    
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            email=user_info["email"],
            username=user_info.get("name", user_info["email"]),
            full_name=user_info.get("name"),
            profile_picture_url=user_info.get("picture"),
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    response = RedirectResponse(url="http://localhost:3000/dashboard")
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return response

# LinkedIn OAuth2 Settings
LINKEDIN_CLIENT_ID = "YOUR_LINKEDIN_CLIENT_ID"
LINKEDIN_CLIENT_SECRET = "YOUR_LINKEDIN_CLIENT_SECRET"
LINKEDIN_REDIRECT_URI = "http://localhost:8000/api/v1/auth/linkedin/callback"

@router.get("/linkedin")
async def linkedin_login():
    return RedirectResponse(
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={LINKEDIN_REDIRECT_URI}&scope=r_liteprofile%20r_emailaddress"
    )

@router.get("/linkedin/callback")
async def linkedin_callback(code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "code": code,
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
                "redirect_uri": LINKEDIN_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        email_response = await client.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    user_info = user_info_response.json()
    email_data = email_response.json()
    email = email_data["elements"][0]["handle~"]["emailAddress"]

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username=user_info.get("localizedFirstName", email),
            full_name=f"{user_info.get('localizedFirstName')} {user_info.get('localizedLastName')}",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        social_account = SocialAccount(
            user_id=user.id,
            provider="linkedin",
            provider_user_id=user_info["id"],
            provider_email=email,
            provider_data=user_info,
        )
        db.add(social_account)
        db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

# GitHub OAuth2 Settings
GITHUB_CLIENT_ID = "YOUR_GITHUB_CLIENT_ID"
GITHUB_CLIENT_SECRET = "YOUR_GITHUB_CLIENT_SECRET"
GITHUB_REDIRECT_URI = "http://localhost:8000/api/v1/auth/github/callback"

@router.get("/github")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_REDIRECT_URI}&scope=user:email"
    )

@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    user_info = user_info_response.json()
    emails = emails_response.json()
    primary_email = next((email["email"] for email in emails if email["primary"]), None)
    email = primary_email or user_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from GitHub")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username=user_info.get("login", email),
            full_name=user_info.get("name"),
            profile_picture_url=user_info.get("avatar_url"),
            github_url=user_info.get("html_url"),
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
