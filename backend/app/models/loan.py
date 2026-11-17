import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_reference = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    offer_id = Column(String(36), ForeignKey("loan_offers.id"), nullable=False)
    principal_paise = Column(BigInteger, nullable=False)
    outstanding_principal_paise = Column(BigInteger, nullable=False)
    outstanding_interest_paise = Column(BigInteger, nullable=False)
    outstanding_penalties_paise = Column(BigInteger, default=0, nullable=False)
    status = Column(String(30), default="PENDING_DISBURSEMENT", nullable=False)  
    # PENDING_DISBURSEMENT, ACTIVE, OVERDUE, FORECLOSED, CLOSED
    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="loans")
    application = relationship("LoanApplication", back_populates="loans")
    offer = relationship("LoanOffer", back_populates="loans")
    instalments = relationship("Instalment", back_populates="loan", cascade="all, delete-orphan", order_by="Instalment.instalment_number")
    disbursements = relationship("Disbursement", back_populates="loan", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="loan", cascade="all, delete-orphan")


class Instalment(Base):
    __tablename__ = "instalments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = Column(String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    instalment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    opening_principal_paise = Column(BigInteger, nullable=False)
    emi_amount_paise = Column(BigInteger, nullable=False)
    principal_component_paise = Column(BigInteger, nullable=False)
    interest_component_paise = Column(BigInteger, nullable=False)
    closing_principal_paise = Column(BigInteger, nullable=False)
    paid_principal_paise = Column(BigInteger, default=0, nullable=False)
    paid_interest_paise = Column(BigInteger, default=0, nullable=False)
    outstanding_amount_paise = Column(BigInteger, nullable=False)
    status = Column(String(20), default="SCHEDULED", nullable=False)  # SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    loan = relationship("Loan", back_populates="instalments")
    allocations = relationship("PaymentAllocation", back_populates="instalment")
