import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import IdempotencyRecord


def compute_payload_hash(payload: Any) -> str:
    """
    Computes deterministic SHA256 hash of JSON-serializable request payload.
    """
    req_str = json.dumps(payload, default=str, sort_keys=True)
    return hashlib.sha256(req_str.encode()).hexdigest()


async def check_idempotency(
    db: AsyncSession,
    idempotency_key: Optional[str],
    request_path: str,
    payload: Any,
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """
    Checks if this idempotency key was previously processed.
    Returns (status_code, response_body_dict) if previously processed, or None.
    """
    if not idempotency_key:
        return None

    stmt = select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if record:
        try:
            body = json.loads(record.response_body)
        except Exception:
            body = {"message": record.response_body}
        return record.response_code, body

    return None


async def save_idempotency(
    db: AsyncSession,
    idempotency_key: Optional[str],
    request_path: str,
    payload: Any,
    response_code: int,
    response_data: Any,
):
    """
    Saves idempotency record upon successful completion of mutative transaction.
    """
    if not idempotency_key:
        return

    req_str = json.dumps(payload, default=str, sort_keys=True)
    req_hash = hashlib.sha256(req_str.encode()).hexdigest()
    resp_str = json.dumps(response_data, default=str)

    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        request_path=request_path,
        request_hash=req_hash,
        response_code=response_code,
        response_body=resp_str,
    )
    db.add(record)
    await db.flush()
