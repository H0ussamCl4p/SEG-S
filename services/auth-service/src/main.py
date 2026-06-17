"""
Authentication Microservice for IIoT Predictive Maintenance
Handles user authentication and JWT token generation with PostgreSQL persistence
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os
import bcrypt
from jose import jwt, JWTError
import uvicorn
from sqlalchemy.orm import Session

# Import database
from src.database import get_db, init_db, User as UserModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def _hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"Warning: Password hashing failed: {e}")
        # Fallback for development
        return "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

def _init_default_users(db: Session):
    """Initialize default admin and operator accounts if they don't exist"""
    # Check if admin exists
    admin = db.query(UserModel).filter(UserModel.username == "admin").first()
    if not admin:
        admin = UserModel(
            username="admin",
            full_name="System Administrator",
            email="admin@iiot.local",
            hashed_password=_hash_password("admin123"),
            role="admin",
            disabled=False
        )
        db.add(admin)
    
    # Check if operator exists
    operator = db.query(UserModel).filter(UserModel.username == "operator").first()
    if not operator:
        operator = UserModel(
            username="operator",
            full_name="Factory Operator",
            email="operator@iiot.local",
            hashed_password=_hash_password("operator123"),
            role="operator",
            disabled=False
        )
        db.add(operator)
    
    db.commit()
    print("✓ Default users initialized (admin, operator)")

# Initialize FastAPI
app = FastAPI(
    title="IIoT Auth Service",
    description="Authentication microservice for user management and JWT tokens",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and default users on startup"""
    try:
        # Create tables
        init_db()
        # Initialize default users
        from src.database import SessionLocal
        db = SessionLocal()
        try:
            _init_default_users(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserInfo(BaseModel):
    username: str
    full_name: str
    email: str
    role: str

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def authenticate_user(username: str, password: str, db: Session):
    """Authenticate user credentials against database"""
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = authenticate_user(request.username, request.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Return token and user info (without password)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }

@app.get("/auth/verify")
async def verify_token(token: str, db: Session = Depends(get_db)):
    """Verify JWT token and return user info"""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    username = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.username == username).first()
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled"
        )
    
    return {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }

@app.post("/auth/logout")
async def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
