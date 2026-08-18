"""Rendering the printable QR poster.

The QR encodes a deep link to the scan landing page rather than the bare code,
so a phone camera opens the site directly with no app in between.
"""

from __future__ import annotations

import io

import segno

from app.core.config import get_settings

#: Path of the SPA route that redeems a scanned code.
SCAN_PATH = "/a"


def poster_url(code: str, *, base_url: str | None = None) -> str:
    """Return the URL encoded in the QR image for ``code``."""
    root = (base_url or get_settings().public_base_url).rstrip("/")
    return f"{root}{SCAN_PATH}/{code}"


def render_svg(code: str, *, base_url: str | None = None, scale: int = 8) -> str:
    """Return an inline SVG QR code for ``code``.

    Error correction level Q keeps the code readable on a poster that may be
    scuffed or partly lit, at a modest size cost.
    """
    qr = segno.make(poster_url(code, base_url=base_url), error="q")
    buffer = io.BytesIO()
    qr.save(
        buffer,
        kind="svg",
        scale=scale,
        border=2,
        dark="#1f2a24",
        light=None,
        svgclass=None,
        lineclass=None,
        xmldecl=False,
        omitsize=True,
    )
    return buffer.getvalue().decode("utf-8")
