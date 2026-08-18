"""Background task that keeps the printed code fresh.

Rotation is also applied lazily on request (:func:`access_service.ensure_active_code`),
so the site stays correct even if this worker is not running. The worker exists
so that a property left idle for a week still shows a rotated poster the moment
someone opens the admin dashboard.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import timedelta

from app.core.clock import utcnow
from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.services import access_service

logger = get_logger(__name__)

#: How often the worker wakes up.
TICK_INTERVAL_SECONDS = 60
#: How often expired visitor sessions are purged.
PURGE_INTERVAL = timedelta(hours=6)


async def _tick(*, purge: bool) -> None:
    """Run one rotation check inside its own transaction."""
    async with get_sessionmaker()() as session:
        await access_service.ensure_active_code(session)
        if purge:
            removed = await access_service.purge_expired_sessions(session)
            if removed:
                logger.info("purged expired guest sessions", extra={"removed": removed})
        await session.commit()


async def run_rotation_worker(stop: asyncio.Event) -> None:
    """Loop until ``stop`` is set, rotating the code when it falls due."""
    last_purge = utcnow()
    logger.info("rotation worker started", extra={"interval_s": TICK_INTERVAL_SECONDS})

    while not stop.is_set():
        try:
            now = utcnow()
            due_for_purge = now - last_purge >= PURGE_INTERVAL
            await _tick(purge=due_for_purge)
            if due_for_purge:
                last_purge = now
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("rotation worker tick failed")

        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=TICK_INTERVAL_SECONDS)

    logger.info("rotation worker stopped")
