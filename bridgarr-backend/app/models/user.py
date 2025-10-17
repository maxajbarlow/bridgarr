"""User model"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class DebridProvider(str, enum.Enum):
    """Supported debrid service providers"""
    REAL_DEBRID = "real-debrid"
    ALL_DEBRID = "alldebrid"
    PREMIUMIZE = "premiumize"
    DEBRID_LINK = "debrid-link"


class User(Base):
    """User account with debrid service integration"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Debrid service integration
    debrid_provider = Column(
        SQLEnum(DebridProvider),
        default=DebridProvider.REAL_DEBRID,
        nullable=False
    )
    debrid_api_token = Column(String(500), nullable=True)
    debrid_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Legacy Real-Debrid fields (deprecated, kept for migration compatibility)
    rd_api_token = Column(String(500), nullable=True)
    rd_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
