import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)  # LOAN, APPLICATION, OFFER, PAYMENT
    entity_id = Column(String(36), nullable=False)
    doc_type = Column(String(50), nullable=False)  # KFS, SANCTION_LETTER, AGREEMENT, RECEIPT, CLOSURE
    title = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    is_watermarked = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(30), default="IN_APP", nullable=False)  # IN_APP, MOCK_SMS, MOCK_EMAIL
    is_read = Column(Boolean, default=False, nullable=False)
    delivery_status = Column(String(30), default="DELIVERED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_reference = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # PAYMENT, LOAN_STATUS, KYC, APP_ISSUE, OTHER
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN", nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    assigned_admin_id = Column(String(36), ForeignKey("admin_users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="support_tickets")
    messages = relationship("SupportMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="SupportMessage.created_at")


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # CUSTOMER, ADMIN
    sender_id = Column(String(36), nullable=False)
    message = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_type = Column(String(20), nullable=False)  # CUSTOMER, ADMIN, SYSTEM
    actor_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False)
    target_entity = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False)
    details = Column(Text, nullable=True)  # JSON or text
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    request_path = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_code = Column(BigInteger, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
