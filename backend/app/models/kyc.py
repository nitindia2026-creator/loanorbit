import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class KYCCase(Base):
    __tablename__ = "kyc_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    id_type = Column(String(50), nullable=False)  # PAN, AADHAAR, PASSPORT
    id_number_masked = Column(String(50), nullable=False)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, VERIFIED, REJECTED, RESUBMISSION_REQUESTED
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="kyc_cases")
    documents = relationship("KYCDocument", back_populates="kyc_case", cascade="all, delete-orphan")
    decisions = relationship("KYCDecision", back_populates="kyc_case", cascade="all, delete-orphan")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kyc_case_id = Column(String(36), ForeignKey("kyc_cases.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String(50), nullable=False)  # ID_FRONT, ID_BACK, SELFIE
    file_path = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    kyc_case = relationship("KYCCase", back_populates="documents")


class KYCDecision(Base):
    __tablename__ = "kyc_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kyc_case_id = Column(String(36), ForeignKey("kyc_cases.id", ondelete="CASCADE"), nullable=False)
    officer_id = Column(String(36), ForeignKey("admin_users.id"), nullable=False)
    decision = Column(String(30), nullable=False)  # VERIFIED, REJECTED, RESUBMISSION_REQUESTED
    reason_code = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    kyc_case = relationship("KYCCase", back_populates="decisions")
