from typing import Any, Optional
from fastapi import HTTPException, status


class LoanOrbitException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": detail,
                "extra": extra or {},
            },
        )


class ResourceNotFoundException(LoanOrbitException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' was not found.",
            error_code="RESOURCE_NOT_FOUND",
        )


class UnauthorizedException(LoanOrbitException):
    def __init__(self, detail: str = "Invalid credentials or unauthorized access."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(LoanOrbitException):
    def __init__(self, detail: str = "You do not have permission to execute this operation."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class BusinessLogicException(LoanOrbitException):
    def __init__(self, detail: str, error_code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
        )


class IdempotencyConflictException(LoanOrbitException):
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation with idempotency key '{key}' has already been processed.",
            error_code="IDEMPOTENCY_CONFLICT",
        )
