from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.profile import CustomerProfile
from app.models.user import User
from app.schemas.customer import ProfileCreateOrUpdate, ProfileResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/me")
async def get_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns user profile and onboarding progress.
    """
    stmt = select(CustomerProfile).where(CustomerProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    return {
        "id": current_user.id,
        "mobile_number": current_user.mobile_number,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "has_profile": profile is not None,
        "profile": ProfileResponse.model_validate(profile) if profile else None,
    }


@router.put("/profile", response_model=ProfileResponse)
async def upsert_customer_profile(
    payload: ProfileCreateOrUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates or updates the customer's onboarding profile.
    """
    stmt = select(CustomerProfile).where(CustomerProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = CustomerProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for k, v in payload.model_dump().items():
            setattr(profile, k, v)

    await db.commit()
    await db.refresh(profile)
    return profile
