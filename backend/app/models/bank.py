import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class BankVerification(Base):
    __tablename__ = "bank_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_holder_name = Column(String(255), nullable=False)
    bank_name = Column(String(100), nullable=False)
    account_number_masked = Column(String(50), nullable=False)
    ifsc_code = Column(String(20), nullable=False)
    status = Column(String(30), default="PENDING", nullable=False)  # VERIFIED, NAME_MISMATCH, INVALID_ACCOUNT, FAILED
    penny_drop_reference = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="bank_verifications")
