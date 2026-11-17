import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_reference = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_version_id = Column(String(36), ForeignKey("loan_product_versions.id"), nullable=False)
    requested_amount_paise = Column(BigInteger, nullable=False)
    requested_tenure_months = Column(Integer, nullable=False)
    purpose = Column(String(255), nullable=False)
    status = Column(String(50), default="SUBMITTED", nullable=False)  
    # SUBMITTED, UNDER_REVIEW, INFO_REQUESTED, APPROVED, REJECTED, OFFER_ACCEPTED, DISBURSED, CANCELLED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="applications")
    product_version = relationship("LoanProductVersion", back_populates="applications")
    underwriting_decisions = relationship("UnderwritingDecision", back_populates="application", cascade="all, delete-orphan")
    offers = relationship("LoanOffer", back_populates="application", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="application")


class UnderwritingDecision(Base):
    __tablename__ = "underwriting_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    underwriter_id = Column(String(36), ForeignKey("admin_users.id"), nullable=False)
    decision = Column(String(30), nullable=False)  # APPROVED, REJECTED, ADDITIONAL_INFO_REQUIRED
    approved_amount_paise = Column(BigInteger, nullable=True)
    approved_tenure_months = Column(Integer, nullable=True)
    approved_rate_bps = Column(Integer, nullable=True)
    rule_engine_score = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=False)
    policy_version = Column(String(50), default="v1.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    application = relationship("LoanApplication", back_populates="underwriting_decisions")
