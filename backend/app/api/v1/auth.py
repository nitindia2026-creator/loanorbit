from datetime import datetime, timezone
import hashlib
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import AdminUser, RefreshToken, User
from app.providers.otp import otp_provider
from app.schemas.auth import (
    AdminLoginRequest,
    OTPRequest,
    OTPResponse,
    OTPVerifyRequest,
    Token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/otp/request", response_model=OTPResponse)
async def request_otp(payload: OTPRequest):
    """
    Simulated OTP delivery for customer demo registration/login.
    """
    result = otp_provider.send_otp(payload.mobile_number)
    return {
        "success": True,
        "message": "Simulated OTP dispatched to mobile number.",
        "delivery_channel": result["delivery_channel"],
        "expires_in_seconds": 300,
        "demo_hint": f"Use test code: {result['code']}",
    }


@router.post("/otp/verify", response_model=Token)
async def verify_otp(payload: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies simulated OTP and returns JWT access and refresh tokens.
    Automatically creates the customer user if first time.
    """
    is_valid = otp_provider.verify_otp(payload.mobile_number, payload.otp_code)
    if not is_valid:
        raise UnauthorizedException("Invalid or expired OTP code.")

    # Find or create user
    stmt = select(User).where(User.mobile_number == payload.mobile_number)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            mobile_number=payload.mobile_number,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()

    # Generate tokens
    access_token = create_access_token(subject=user.id, role="CUSTOMER")
    refresh_token = create_refresh_token(subject=user.id, role="CUSTOMER")

    # Persist refresh token hash
    rf_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=rf_hash,
        expires_at=datetime.now(timezone.utc),
    )
    db.add(db_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user.id,
        "role": "CUSTOMER",
    }


@router.post("/admin/login", response_model=Token)
async def admin_login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Admin authentication using Argon2id/bcrypt hashed passwords and RBAC roles.
    """
    stmt = select(AdminUser).where(AdminUser.username == payload.username)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise UnauthorizedException("Invalid username or password.")

    if not admin.is_active:
        raise UnauthorizedException("This administrative account is disabled.")

    access_token = create_access_token(subject=admin.id, role=admin.role.value)
    refresh_token = create_refresh_token(subject=admin.id, role=admin.role.value)

    rf_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db_token = RefreshToken(
        admin_user_id=admin.id,
        token_hash=rf_hash,
        expires_at=datetime.now(timezone.utc),
    )
    db.add(db_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": admin.id,
        "role": admin.role.value,
    }
