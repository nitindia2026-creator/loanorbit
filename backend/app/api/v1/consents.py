from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.consent import Consent
from app.models.user import User
from app.schemas.customer import ConsentCreate, ConsentResponse

router = APIRouter(prefix="/consents", tags=["Consents"])


@router.get("", response_model=List[ConsentResponse])
async def list_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Consent).where(Consent.user_id == current_user.id).order_by(Consent.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ConsentResponse)
async def record_consent(
    payload: ConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    consent = Consent(
        user_id=current_user.id,
        purpose=payload.purpose,
        policy_version=payload.policy_version,
        status=payload.status,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent
