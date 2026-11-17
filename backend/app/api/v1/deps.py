from typing import AsyncGenerator, Callable, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ForbiddenException, UnauthorizedException
from app.core.permissions import PermissionEnum, RoleEnum, role_has_permission
from app.core.security import decode_token
from app.models.user import AdminUser, User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedException("Authentication token is required.")

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type. Access token required.")
        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id:
            raise UnauthorizedException("Token payload missing user identifier.")
    except (JWTError, Exception):
        raise UnauthorizedException("Could not validate authorization token.")

    # Fetch customer from DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found.")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive.")

    return user


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not credentials:
        raise UnauthorizedException("Admin authorization token is required.")

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type.")
        admin_id = payload.get("sub")
        role = payload.get("role")
        if not admin_id or not role:
            raise UnauthorizedException("Malformed token claims.")
    except (JWTError, Exception):
        raise UnauthorizedException("Could not validate admin authorization token.")

    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin:
        raise UnauthorizedException("Admin user account not found.")
    if not admin.is_active:
        raise ForbiddenException("Admin account is deactivated.")

    return admin


def require_permission(permission: PermissionEnum) -> Callable:
    async def permission_checker(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if not role_has_permission(admin.role, permission):
            raise ForbiddenException(
                f"Role '{admin.role.value}' does not possess required permission '{permission.value}'."
            )
        return admin

    return permission_checker
