import hashlib
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import BusinessLogicException
from app.models.kyc import KYCCase, KYCDocument
from app.models.user import User
from app.providers.kyc import kyc_provider
from app.schemas.kyc import KYCCaseResponse

router = APIRouter(prefix="/kyc", tags=["KYC Simulation"])


@router.get("/status", response_model=Optional[KYCCaseResponse])
async def get_kyc_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(KYCCase)
        .where(KYCCase.user_id == current_user.id)
        .options(selectinload(KYCCase.documents))
        .order_by(KYCCase.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.post("/submit", response_model=KYCCaseResponse)
async def submit_synthetic_kyc(
    id_type: str = Form(..., pattern=r"^(PAN|AADHAAR|PASSPORT)$"),
    id_number: str = Form(...),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits synthetic KYC document for deterministic simulation.
    Never processes real government IDs.
    """
    # Read file content safely
    content = await document_file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise BusinessLogicException("File size exceeds 5MB limit.")

    file_hash = hashlib.sha256(content).hexdigest()
    masked_id = f"XXXXXX{id_number[-4:]}" if len(id_number) >= 4 else "XXXX"

    # Evaluate mock provider
    mock_result = kyc_provider.verify_document(id_type, id_number)
    status_outcome = mock_result["status"]  # VERIFIED, REJECTED, MANUAL_REVIEW -> PENDING

    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    file_name = f"kyc_{uuid.uuid4().hex}_{document_file.filename}"
    file_path = os.path.join(settings.STORAGE_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(content)

    kyc_case = KYCCase(
        user_id=current_user.id,
        id_type=id_type,
        id_number_masked=masked_id,
        status="VERIFIED" if status_outcome == "VERIFIED" else "PENDING",
        rejection_reason=mock_result.get("message") if status_outcome == "REJECTED" else None,
    )
    db.add(kyc_case)
    await db.flush()

    doc = KYCDocument(
        kyc_case_id=kyc_case.id,
        doc_type="ID_FRONT",
        file_path=file_path,
        file_hash=file_hash,
        file_size_bytes=len(content),
        mime_type=document_file.content_type or "application/octet-stream",
    )
    db.add(doc)
    await db.commit()

    # Reload with relationships
    stmt = (
        select(KYCCase)
        .where(KYCCase.id == kyc_case.id)
        .options(selectinload(KYCCase.documents))
    )
    reloaded = await db.execute(stmt)
    return reloaded.scalar_one()
