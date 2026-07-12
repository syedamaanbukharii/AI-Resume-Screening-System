"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from backend.api.v1.router import api_router
from backend.core.config import settings
from backend.core.exceptions import register_exception_handlers
from backend.core.logging_config import configure_logging
from backend.core.middleware import register_middleware
from backend.database.engine import engine

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging on startup and dispose the engine on shutdown."""
    configure_logging()
    logger.info("startup", app=settings.APP_NAME, env=settings.APP_ENV)
    yield
    await engine.dispose()
    logger.info("shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
