"""HTTP middleware: CORS, request-id binding, and request/response logging."""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.config import settings

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a UUID request id, bind it to structlog, and echo it in headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Bind a request id for the lifetime of the request."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status, and latency for each request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Time the request and emit a structured access log line."""
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
        )
        return response


def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app in the correct order."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
