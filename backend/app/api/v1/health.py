from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Standard structured health check endpoint for uptime and monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "is_sandbox_demo": settings.IS_SANDBOX_DEMO,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "UP",
            "financial_engine": "UP",
            "mock_providers": "UP",
        }
    }
