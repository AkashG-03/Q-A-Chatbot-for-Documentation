# backend/auth.py
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from backend.db import db_session
from backend.models import User, DoctorsRegistry

# -----------------------------
# Password Utilities
# -----------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(password, hashed)


# -----------------------------
# JWT Configuration
# -----------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for user"""
    to_encode = {"sub": str(user_id), "email": email, "iat": datetime.utcnow()}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)


# -----------------------------
# Authenticated User Class
# -----------------------------

class AuthUser:
    """Authenticated user class for dependency injection"""
    def __init__(self, id: int, email: str, role: str = "general", legal_no: str = None, full_name: str = None):
        self.id = id
        self.email = email
        self.role = role
        self.legal_no = legal_no
        self.full_name = full_name
    
    def is_professional(self) -> bool:
        """Check if user has professional role"""
        return self.role == "professional"
    
    def can_upload(self) -> bool:
        """Check if user can upload documents"""
        return self.role in ["professional", "admin"]


# -----------------------------
# Authentication Flows
# -----------------------------

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    """Get current authenticated user from JWT token"""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id_str is None or email is None:
            raise cred_exc
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise cred_exc

    with db_session() as db:
        user = db.get(User, user_id)
        if not user or user.email != email:
            raise cred_exc
        return AuthUser(
            id=user.id, 
            email=user.email, 
            role=user.role,
            legal_no=user.legal_no,
            full_name=user.full_name
        )


# -----------------------------
# Doctor Registry Verification
# -----------------------------

def verify_doctor_credentials(legal_no: str, phone_number: str) -> Optional[dict]:
    """Verify doctor credentials against government registry"""
    with db_session() as db:
        doctor = db.execute(
            select(DoctorsRegistry).where(
                DoctorsRegistry.legal_no == legal_no,
                DoctorsRegistry.phone_number == phone_number,
                DoctorsRegistry.license_status == "active"
            )
        ).scalar_one_or_none()
        
        if doctor:
            return {
                "legal_no": doctor.legal_no,
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
                "verified": True
            }
        return None


# -----------------------------
# Role-Based Dependencies
# -----------------------------

async def get_professional_user(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Dependency to ensure user has professional privileges"""
    if not user.can_upload():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional account required for this action"
        )
    return user
