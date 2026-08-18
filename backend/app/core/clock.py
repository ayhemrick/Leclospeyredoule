"""Single source of "now".

Routing every timestamp through one function keeps the code timezone-aware and
gives the tests one place to freeze or advance time.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)
