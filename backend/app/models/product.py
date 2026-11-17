import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    versions = relationship("LoanProductVersion", back_populates="product", cascade="all, delete-orphan")


class LoanProductVersion(Base):
    __tablename__ = "loan_product_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("loan_products.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    min_principal_paise = Column(BigInteger, nullable=False)
    max_principal_paise = Column(BigInteger, nullable=False)
    available_tenures_months = Column(String(100), nullable=False)  # JSON or comma-separated e.g. "3,6,12"
    annual_nominal_interest_rate_bps = Column(Integer, nullable=False)  # 1800 = 18.00%
    processing_fee_type = Column(String(20), default="PERCENTAGE", nullable=False)  # PERCENTAGE or FIXED
    processing_fee_value = Column(Integer, nullable=False)  # Bps (e.g. 200 = 2%) or Fixed Paise
    gst_rate_bps = Column(Integer, default=1800, nullable=False)  # 1800 = 18%
    late_charge_daily_bps = Column(Integer, default=5, nullable=False)  # 5 = 0.05%/day
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("LoanProduct", back_populates="versions")
    applications = relationship("LoanApplication", back_populates="product_version")
