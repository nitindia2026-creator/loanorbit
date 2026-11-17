from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "loanorbit_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task
def generate_document_async(doc_type: str, entity_id: str):
    """
    Background worker task to generate PDF documents asynchronously.
    """
    return {"status": "SUCCESS", "doc_type": doc_type, "entity_id": entity_id}
