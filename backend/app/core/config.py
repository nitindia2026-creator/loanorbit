from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "LOANORBIT"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-loanorbit-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./loanorbit.db"
    SYNC_DATABASE_URL: str = "sqlite:///./loanorbit.db"

    # Redis & Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage
    STORAGE_DIR: str = "./storage/private"
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB

    # Sandbox
    IS_SANDBOX_DEMO: bool = True
    MOCK_OTP_DEFAULT_CODE: str = "123456"
    ENABLE_MOCK_LENDER_AUTO_DISBURSE: bool = True
    ENABLE_MOCK_PAYMENT_AUTO_SUCCESS: bool = True

    # Seed Super Admin
    SUPER_ADMIN_USERNAME: str = "superadmin"
    SUPER_ADMIN_EMAIL: str = "superadmin@loanorbit.demo"
    SUPER_ADMIN_PASSWORD: str = "AdminSecurePass123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
