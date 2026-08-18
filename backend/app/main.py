"""FastAPI application factory and process lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine, get_sessionmaker
from app.services.rotation_worker import run_rotation_worker
from app.services.seed import seed_all

logger = get_logger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # The API only ever answers JSON; a strict policy costs nothing here.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Seed the database and run the rotation worker for the app's lifetime."""
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.assert_production_ready()

    async with get_sessionmaker()() as session:
        await seed_all(session)
        await session.commit()

    stop = asyncio.Event()
    worker = asyncio.create_task(run_rotation_worker(stop), name="rotation-worker")
    app.state.rotation_worker = worker
    try:
        yield
    finally:
        stop.set()
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker
        await dispose_engine()


def create_app() -> FastAPI:
    """Build the configured application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Clos Peyredoule API",
        version="0.1.0",
        summary="Visitor site for a Blaye property, with rotating QR access control.",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
        max_age=600,
    )

    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Attach hardening headers to every response."""
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Log the traceback and return an opaque 500 to the client."""
        logger.exception("unhandled error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    async def health() -> dict[str, Any]:
        """Return service liveness, used by Docker and CI."""
        return {"status": "ok", "environment": settings.app_env}

    app.include_router(api_router)
    return app


app = create_app()
