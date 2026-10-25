from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(64), nullable=False) # LAND_LEASE_DEED, FIRE_SAFETY_NOC, BUILDING_STABILITY, OCCUPANCY_CERTIFICATE, POLLUTION_NOC
    title = Column(String(255), nullable=False)
    document_number = Column(String(128), nullable=True)
    issuing_authority = Column(String(128), nullable=True)
    issue_date = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True) # Expiry date tracked for renewals (nullable for perpetual docs)
    renewal_required = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True) # ACTIVE, EXPIRING_SOON, RENEWAL_SUBMITTED, VERIFIED, EXPIRED
    current_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    institution = relationship("Institution", back_populates="documents")
    application = relationship("Application", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document_record", cascade="all, delete-orphan", order_by="DocumentVersion.version.desc()")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_record_id = Column(Integer, ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    storage_key = Column(String(255), nullable=True, index=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)
    checksum_sha256 = Column(String(64), nullable=False)
    renewal_reason = Column(Text, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    verification_status = Column(String(32), default="PENDING", nullable=False) # PENDING, VERIFIED, REJECTED
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    document_record = relationship("DocumentRecord", back_populates="versions")
