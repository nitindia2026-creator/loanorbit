import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(String(100), nullable=False)  # PRIVACY_POLICY, TERMS, KYC_FETCH, LENDER_SHARING, NOTIFICATIONS
    policy_version = Column(String(20), nullable=False)
    status = Column(String(20), default="ACCEPTED", nullable=False)  # ACCEPTED, REJECTED, REVOKED
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="consents")
