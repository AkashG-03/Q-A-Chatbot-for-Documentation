# backend/db.py
from __future__ import annotations

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# -----------------------------
# Environment Setup
# -----------------------------

load_dotenv()

# -----------------------------
# Database URL Configuration
# -----------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "chatbotdb")
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# -----------------------------
# Engine & Session
# -----------------------------

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# -----------------------------
# Session Context Manager
# -----------------------------

@contextmanager
def db_session():
    """Database session context manager"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# -----------------------------
# Database Initialization
# -----------------------------

def init_database():
    """Initialize database tables"""
    from backend.models import Base
    Base.metadata.create_all(bind=engine)
