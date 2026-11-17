import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Disbursement(Base):
    __tablename__ = "disbursements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = Column(String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    bank_verification_id = Column(String(36), ForeignKey("bank_verifications.id"), nullable=False)
    mock_provider_reference = Column(String(100), nullable=True)
    status = Column(String(30), default="INITIATED", nullable=False)  # INITIATED, SUCCESS, FAILED
    failure_reason = Column(Text, nullable=True)
    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    loan = relationship("Loan", back_populates="disbursements")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = Column(String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    payment_method = Column(String(50), default="UPI_MOCK", nullable=False)
    status = Column(String(30), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, PENDING, REVERSED
    provider_reference = Column(String(100), nullable=True)
    paid_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    loan = relationship("Loan", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    instalment_id = Column(String(36), ForeignKey("instalments.id", ondelete="CASCADE"), nullable=False)
    allocated_principal_paise = Column(BigInteger, default=0, nullable=False)
    allocated_interest_paise = Column(BigInteger, default=0, nullable=False)
    allocated_charges_paise = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    instalment = relationship("Instalment", back_populates="allocations")
