from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False) # e.g. "1-3324901"
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False, default="ENGINEERING_AND_TECHNOLOGY")
    state = Column(String(64), nullable=False)
    region = Column(String(64), index=True, nullable=False) # Western, Northern, Southern, etc.
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")
    undertakings = relationship("ComplianceUndertaking", back_populates="institution", cascade="all, delete-orphan")
    documents = relationship("DocumentRecord", back_populates="institution", cascade="all, delete-orphan")
