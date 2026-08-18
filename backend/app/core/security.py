"""Password hashing, token minting and privacy-preserving hashes.

Two independent credential systems live here:

* **Administrators** authenticate with e-mail and password (Argon2id) and then
  carry a short-lived JWT access token plus a refresh token, both in
  ``HttpOnly`` cookies, guarded by a double-submit CSRF token.
* **Visitors** never authenticate. Scanning the property QR code exchanges the
  posted code for an opaque, high-entropy session token that is only stored
  hashed server-side, so a database leak cannot be replayed against the site.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

JWT_ALGORITHM: Final = "HS256"
JWT_ISSUER: Final = "clos-peyredoule"
TokenKind = Literal["access", "refresh"]

# Argon2id parameters follow the OWASP Password Storage Cheat Sheet
# (m=19 MiB, t=2, p=1), matching the RFC 9106 second recommended profile.
_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


@dataclass(frozen=True, slots=True)
class DecodedToken:
    """A verified JWT payload."""

    subject: uuid.UUID
    kind: TokenKind
    jti: uuid.UUID
    expires_at: datetime
    #: Matches ``AdminUser.token_epoch``; a mismatch means the account has
    #: changed password or been signed out everywhere since this was minted.
    epoch: str


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired or of the wrong kind."""


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Return an Argon2id hash for ``password``."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check ``password`` against ``password_hash`` without leaking timing."""
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError, VerificationError, InvalidHashError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Whether a stored hash uses outdated Argon2 parameters."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


# ---------------------------------------------------------------------------
# JWT (administrators)
# ---------------------------------------------------------------------------
def create_token(
    subject: uuid.UUID, kind: TokenKind, *, epoch: str
) -> tuple[str, uuid.UUID, datetime]:
    """Mint a signed JWT.

    Args:
        subject: the administrator's id.
        kind: ``"access"`` for API calls, ``"refresh"`` to obtain a new pair.
        epoch: the account's current ``token_epoch``, so a password change
            invalidates tokens minted before it.

    Returns:
        The encoded token, its ``jti`` (so refresh tokens can be revoked
        server-side) and its expiry.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = (
        timedelta(minutes=settings.access_token_ttl_minutes)
        if kind == "access"
        else timedelta(days=settings.refresh_token_ttl_days)
    )
    expires_at = now + ttl
    jti = uuid.uuid4()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "typ": kind,
        "jti": str(jti),
        "epo": epoch,
        "iss": JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.app_secret_key, algorithm=JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str, expected_kind: TokenKind) -> DecodedToken:
    """Verify a JWT signature, issuer, expiry and kind.

    Raises:
        TokenError: if any check fails.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti", "iss", "epo"]},
        )
    except jwt.PyJWTError as exc:  # expired, bad signature, missing claim...
        raise TokenError(str(exc)) from exc

    if payload.get("typ") != expected_kind:
        raise TokenError(f"expected a {expected_kind} token")
    try:
        return DecodedToken(
            subject=uuid.UUID(payload["sub"]),
            kind=expected_kind,
            jti=uuid.UUID(payload["jti"]),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            epoch=str(payload["epo"]),
        )
    except (KeyError, ValueError) as exc:
        raise TokenError("malformed token payload") from exc


# ---------------------------------------------------------------------------
# Opaque tokens (visitors, CSRF, QR codes)
# ---------------------------------------------------------------------------
def generate_opaque_token(nbytes: int = 32) -> str:
    """Return a URL-safe random token carrying at least ``nbytes`` of entropy."""
    return secrets.token_urlsafe(nbytes)


def generate_access_code() -> str:
    """Return the short, URL-safe code embedded in the property QR poster.

    Kept to 16 random bytes (128 bits, 22 characters) so the printed QR code
    stays low-density and scans reliably from a wall-mounted poster.
    """
    return secrets.token_urlsafe(16)


def hash_secret(value: str) -> str:
    """Keyed hash used to store visitor session tokens at rest.

    HMAC with the application secret means a stolen database alone cannot be
    used to forge a session cookie.
    """
    settings = get_settings()
    return hmac.new(
        settings.app_secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def pseudonymise_ip(ip: str | None) -> str | None:
    """Return a truncated keyed hash of a client IP, or ``None``.

    Storing the hash keeps abuse investigation possible (repeat scans from one
    address) without retaining a directly identifying value.
    """
    if not ip:
        return None
    return hash_secret(f"ip:{ip}")[:32]


def constant_time_equals(left: str, right: str) -> bool:
    """Compare two strings without leaking their content through timing."""
    return hmac.compare_digest(left, right)
