import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class LoanOffer(Base):
    __tablename__ = "loan_offers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    offer_reference = Column(String(50), unique=True, index=True, nullable=False)
    offered_amount_paise = Column(BigInteger, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    annual_nominal_interest_rate_bps = Column(Integer, nullable=False)
    monthly_emi_paise = Column(BigInteger, nullable=False)
    processing_fee_paise = Column(BigInteger, nullable=False)
    gst_paise = Column(BigInteger, nullable=False)
    net_disbursement_paise = Column(BigInteger, nullable=False)
    total_repayable_paise = Column(BigInteger, nullable=False)
    apr_bps = Column(Integer, nullable=False)
    status = Column(String(30), default="ISSUED", nullable=False)  # ISSUED, ACCEPTED, REJECTED, EXPIRED
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("LoanApplication", back_populates="offers")
    loans = relationship("Loan", back_populates="offer")
