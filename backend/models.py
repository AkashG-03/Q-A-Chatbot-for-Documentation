# backend/models.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

# -----------------------------
# Enums (simple helpers first)
# -----------------------------
class UserRole(str, enum.Enum):
    GENERAL = "general"
    PROFESSIONAL = "professional"
    ADMIN = "admin"

class LicenseStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class OtpStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"

# -----------------------------
# Core User & Registry Models
# -----------------------------
class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), default=UserRole.GENERAL.value)
    legal_no = Column(String(50), nullable=True)  # Doctor license number
    phone_number = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    otp_verifications = relationship("OtpVerification", back_populates="user", cascade="all, delete-orphan")


class DoctorsRegistry(Base):
    """Government registry of licensed doctors"""
    __tablename__ = "doctors_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legal_no = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    specialization = Column(String(255), nullable=True)
    license_status = Column(String(20), default=LicenseStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# -----------------------------
# OTP Verification
# -----------------------------
class OtpVerification(Base):
    """OTP verification model for professional user registration"""
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    otp_code = Column(String(6), nullable=False)
    status = Column(String(20), default=OtpStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Store registration data temporarily
    registration_data = Column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="otp_verifications")

    @property
    def is_expired(self) -> bool:
        """Check if OTP has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def attempts_exhausted(self) -> bool:
        """Check if maximum attempts have been reached"""
        return self.attempts >= self.max_attempts

# -----------------------------
# Chat System
# -----------------------------
class ChatSession(Base):
    """Chat session model for organizing conversations"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="New chat")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

class Message(Base):
    """Message model for storing chat interactions"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

# -----------------------------
# Documents
# -----------------------------
class Document(Base):
    """Document model for tracking uploaded files"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Only professionals
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False)
    doc_type = Column(String(50), default="medical", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
