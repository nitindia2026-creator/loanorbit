import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_code = Column(String(50), unique=True, index=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(30), nullable=False)  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    balance_paise = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lines = relationship("JournalLine", back_populates="account")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_reference = Column(String(50), unique=True, index=True, nullable=False)
    entry_type = Column(String(50), nullable=False)  # DISBURSEMENT, REPAYMENT, FEE_ACCRUAL, REVERSAL
    description = Column(Text, nullable=False)
    posted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lines = relationship("JournalLine", back_populates="journal_entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(String(36), ForeignKey("ledger_accounts.id"), nullable=False)
    entry_direction = Column(String(10), nullable=False)  # DEBIT or CREDIT
    amount_paise = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("LedgerAccount", back_populates="lines")
