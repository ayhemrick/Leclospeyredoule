"""Unit tests for the security and QR primitives."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import get_settings
from app.services import qr_service


def test_password_hash_is_salted_and_verifiable() -> None:
    first = security.hash_password("correct horse battery staple")
    second = security.hash_password("correct horse battery staple")

    assert first != second  # distinct salts
    assert security.verify_password("correct horse battery staple", first)
    assert not security.verify_password("wrong password", first)


def test_verify_password_survives_a_corrupt_hash() -> None:
    assert security.verify_password("anything", "not-an-argon2-hash") is False
    assert security.password_needs_rehash("not-an-argon2-hash") is True


def test_token_round_trip() -> None:
    subject = uuid.uuid4()
    token, jti, expires_at = security.create_token(subject, "access", epoch="epoch-1")

    decoded = security.decode_token(token, "access")
    assert decoded.subject == subject
    assert decoded.jti == jti
    assert decoded.epoch == "epoch-1"
    assert decoded.expires_at == expires_at.replace(microsecond=0)


def test_access_token_is_not_accepted_as_refresh() -> None:
    token, _, _ = security.create_token(uuid.uuid4(), "access", epoch="e")
    with pytest.raises(security.TokenError):
        security.decode_token(token, "refresh")


def test_expired_token_is_refused() -> None:
    settings = get_settings()
    payload = {
        "sub": str(uuid.uuid4()),
        "typ": "access",
        "jti": str(uuid.uuid4()),
        "epo": "e",
        "iss": security.JWT_ISSUER,
        "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, settings.app_secret_key, algorithm=security.JWT_ALGORITHM)

    with pytest.raises(security.TokenError):
        security.decode_token(token, "access")


def test_token_signed_with_another_key_is_refused() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "typ": "access",
        "jti": str(uuid.uuid4()),
        "epo": "e",
        "iss": security.JWT_ISSUER,
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
    }
    # At least 32 bytes, or PyJWT warns about the key length (which the suite
    # treats as an error) before we get to the assertion we care about.
    token = jwt.encode(payload, "a-completely-different-secret-of-sufficient-length", "HS256")

    with pytest.raises(security.TokenError):
        security.decode_token(token, "access")


def test_unsigned_token_is_refused() -> None:
    """A token with alg=none must not be trusted."""
    payload = {"sub": str(uuid.uuid4()), "typ": "access", "jti": str(uuid.uuid4()), "epo": "e"}
    token = jwt.encode(payload, key="", algorithm="none")

    with pytest.raises(security.TokenError):
        security.decode_token(token, "access")


def test_access_codes_are_unique_and_url_safe() -> None:
    codes = {security.generate_access_code() for _ in range(200)}
    assert len(codes) == 200
    assert all(code.isascii() and "/" not in code and "+" not in code for code in codes)


def test_hash_secret_is_stable_and_hides_the_value() -> None:
    digest = security.hash_secret("token-value")
    assert digest == security.hash_secret("token-value")
    assert digest != security.hash_secret("other-value")
    assert "token-value" not in digest


def test_ip_pseudonymisation() -> None:
    assert security.pseudonymise_ip(None) is None
    hashed = security.pseudonymise_ip("203.0.113.7")
    assert hashed is not None
    assert "203.0.113.7" not in hashed
    assert len(hashed) == 32


def test_poster_url_points_at_the_scan_route() -> None:
    url = qr_service.poster_url("abc123", base_url="https://clos-peyredoule.fr/")
    assert url == "https://clos-peyredoule.fr/a/abc123"


def test_qr_svg_is_renderable() -> None:
    svg = qr_service.render_svg("abc123", base_url="https://clos-peyredoule.fr")
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "path" in svg
