import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ResourceNotFoundException
from app.models.document import SupportMessage, SupportTicket
from app.models.user import User
from app.schemas.ledger import SupportMessageCreate, SupportTicketCreate, SupportTicketResponse

router = APIRouter(prefix="/support", tags=["Customer Support"])


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_my_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SupportTicket)
        .where(SupportTicket.user_id == current_user.id)
        .options(selectinload(SupportTicket.messages))
        .order_by(SupportTicket.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/tickets", response_model=SupportTicketResponse)
async def create_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = SupportTicket(
        ticket_reference=f"TCK-{uuid.uuid4().hex[:6].upper()}",
        user_id=current_user.id,
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
        status="OPEN",
    )
    db.add(ticket)
    await db.flush()

    msg = SupportMessage(
        ticket_id=ticket.id,
        sender_type="CUSTOMER",
        sender_id=current_user.id,
        message=payload.description,
    )
    db.add(msg)
    await db.commit()

    stmt = select(SupportTicket).where(SupportTicket.id == ticket.id).options(selectinload(SupportTicket.messages))
    res = await db.execute(stmt)
    return res.scalar_one()


@router.post("/tickets/{id}/messages")
async def post_message(
    id: str,
    payload: SupportMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupportTicket).where(SupportTicket.id == id, SupportTicket.user_id == current_user.id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise ResourceNotFoundException("SupportTicket", id)

    msg = SupportMessage(
        ticket_id=ticket.id,
        sender_type="CUSTOMER",
        sender_id=current_user.id,
        message=payload.message,
    )
    db.add(msg)
    await db.commit()
    return {"success": True, "message_id": msg.id}
