from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class StatutoryOrder(Base):
    __tablename__ = "statutory_orders"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)

    order_number = Column(String(128), unique=True, nullable=False, index=True)
    decision = Column(String(32), nullable=False, index=True) # APPROVED or REJECTED
    status = Column(String(32), default="ACTIVE", nullable=False, index=True) # ACTIVE, SUPERSEDED, REVOKED
    version = Column(Integer, default=1, nullable=False) # 1, 2, 3...

    order_date = Column(Date, nullable=False)
    decision_recorded_at = Column(DateTime, nullable=False)

    issued_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    issued_by_name = Column(String(128), nullable=False)
    issued_by_designation = Column(String(128), default="Member Secretary / Competent Authority, AICTE", nullable=False)

    decision_remarks = Column(Text, nullable=False)
    conditions = Column(JSON, default=list, nullable=False)
    reference_identifiers = Column(JSON, default=dict, nullable=False)

    pdf_filename = Column(String(255), nullable=False)
    pdf_storage_key = Column(String(255), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    verification_token = Column(String(64), unique=True, nullable=False, index=True)
    template_version = Column(String(32), default="1.0.0", nullable=False)

    signature_status = Column(String(64), default="UNSIGNED_PROTOTYPE", nullable=False)
    signing_provider = Column(String(64), default="NONE_PROTOTYPE_MODE", nullable=False)
    signing_metadata = Column(JSON, default=dict, nullable=False)

    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    superseded_by_order_id = Column(Integer, ForeignKey("statutory_orders.id", ondelete="SET NULL"), nullable=True)
    superseded_at = Column(DateTime, nullable=True)
    superseding_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("Application", foreign_keys=[application_id])
    institution = relationship("Institution", foreign_keys=[institution_id])
    issued_by = relationship("User", foreign_keys=[issued_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])
    superseded_by_order = relationship("StatutoryOrder", remote_side=[id], foreign_keys=[superseded_by_order_id])

    @property
    def application_number(self) -> str:
        return self.application.application_number if self.application else ""

    @property
    def institution_name(self) -> str:
        return self.institution.name if self.institution else ""

    @property
    def pdf_url(self) -> str:
        return f"/api/orders/{self.id}/download"

    @property
    def verification_url(self) -> str:
        return f"/verify-order?token={self.verification_token}"

    @property
    def signature_disclaimer(self) -> str:
        return (
            "This document is an UNSIGNED_PROTOTYPE generated for regulatory workflow evaluation under "
            "AICTE SIH 2026 PS 26262. It does not carry a legally binding digital signature under the Information "
            "Technology Act, 2000. Official statutory issuance requires integration with a licensed Certifying "
            "Authority (CCA) Digital Signature Certificate (DSC) or Aadhaar e-Sign gateway."
        )

