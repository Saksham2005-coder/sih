from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class EVCInspection(Base):
    __tablename__ = "evc_inspections"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_type = Column(String(32), default="PHYSICAL_ONSITE", nullable=False) # PHYSICAL_ONSITE, VIRTUAL_REMOTE
    scheduled_date = Column(DateTime, nullable=True, index=True)
    convener_name = Column(String(128), nullable=True) # E.g. "Prof. Rajesh Sharma (IIT Bombay)"
    expert_member_name = Column(String(128), nullable=True) # E.g. "Dr. Ananya Sen (VJTI)"
    status = Column(String(32), default="PENDING_ASSIGNMENT", nullable=False) # PENDING_ASSIGNMENT, SCHEDULED, IN_PROGRESS, REPORT_SUBMITTED, DEFICIENCY_NOTED, RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION
    report_url = Column(String(512), nullable=True)
    report_notes = Column(Text, nullable=True)
    recommendation = Column(String(64), nullable=True) # RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION, DEFICIENCY_NOTED
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", back_populates="evc_inspections")
