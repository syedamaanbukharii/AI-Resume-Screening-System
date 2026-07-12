"""Application exception hierarchy and FastAPI exception handlers."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class AppException(Exception):
    """Base application exception carrying an HTTP status and error code."""

    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        """Initialize the exception with status, human detail, and machine code."""
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, detail: str = "Resource not found") -> None:
        """Initialize a 404 error."""
        super().__init__(404, detail, "not_found")


class UnauthorizedException(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        """Initialize a 401 error."""
        super().__init__(401, detail, "unauthorized")


class ForbiddenException(AppException):
    """Raised when an authenticated user lacks permission."""

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        """Initialize a 403 error."""
        super().__init__(403, detail, "forbidden")


class ConflictException(AppException):
    """Raised when a resource conflicts with existing state."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        """Initialize a 409 error."""
        super().__init__(409, detail, "conflict")


class ValidationException(AppException):
    """Raised when input fails business validation."""

    def __init__(self, detail: str = "Validation failed") -> None:
        """Initialize a 422 error."""
        super().__init__(422, detail, "validation_error")


def register_exception_handlers(app: FastAPI) -> None:
    """Register JSON exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Serialize an AppException to a structured JSON response."""
        logger.warning(
            "app_exception",
            error_code=exc.error_code,
            detail=exc.detail,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "detail": exc.detail}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Serialize a request-validation error to a consistent envelope."""
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "detail": exc.errors()}},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler that never leaks internals to the client."""
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "detail": "Internal server error"}},
        )
