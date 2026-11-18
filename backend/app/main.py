from contextlib import asynccontextmanager
import logging
import os
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    admin,
    applications,
    auth,
    bank,
    consents,
    customers,
    disbursements,
    documents,
    eligibility,
    health,
    kyc,
    ledger,
    loans,
    offers,
    products,
    repayments,
    support,
    underwriting,
)
from app.core.config import settings
from app.core.database import Base, async_engine
from app.core.errors import LoanOrbitException
from app.core.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure private storage directory exists
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)

    # Create tables automatically on startup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Optionally seed database if explicitly enabled via AUTO_SEED env
    if os.getenv("AUTO_SEED", "false").lower() == "true":
        try:
            from app.scripts.seed import run_seed
            await run_seed()
        except Exception as e:
            logging.getLogger("loanorbit").warning(f"Startup database seed skipped: {e}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LOANORBIT — Complete Digital Lending Platform (Functional Sandbox Demo)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware - Support dynamic origins and credentialed browser requests
cors_origins = settings.BACKEND_CORS_ORIGINS
allow_origin_regex = None
if "*" in cors_origins:
    allow_origin_regex = r"^https?://.*"
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    return response


# Global Exception Handler
@app.exception_handler(LoanOrbitException)
async def loanorbit_exception_handler(request: Request, exc: LoanOrbitException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


# Include API v1 Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(customers.router, prefix=settings.API_V1_STR)
app.include_router(consents.router, prefix=settings.API_V1_STR)
app.include_router(kyc.router, prefix=settings.API_V1_STR)
app.include_router(bank.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(eligibility.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(underwriting.router, prefix=settings.API_V1_STR)
app.include_router(offers.router, prefix=settings.API_V1_STR)
app.include_router(disbursements.router, prefix=settings.API_V1_STR)
app.include_router(loans.router, prefix=settings.API_V1_STR)
app.include_router(repayments.router, prefix=settings.API_V1_STR)
app.include_router(ledger.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(support.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": "Your Credit Journey, Clearly Guided.",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online",
        "mode": "SYNTHETIC_SANDBOX_DEMO",
    }
