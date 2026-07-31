from __future__ import annotations

import os
from typing import Any

import jwt
from jwt import InvalidTokenError


class SecurityError(Exception):
    pass


def extract_bearer_token(headers: dict[str, str]) -> str:
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header:
        raise SecurityError("Missing Authorization header")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise SecurityError("Authorization header must use Bearer token")
    return parts[1].strip()


def validate_jwt_token(
    token: str,
    audience: str,
    issuer: str,
    hs256_secret: str | None,
    allow_test_mode: bool = False,
) -> dict[str, Any]:
    test_mode_token = os.getenv("TEST_MODE_TOKEN")
    if allow_test_mode and test_mode_token and token == test_mode_token:
        return {"sub": "test-user", "scope": "test", "mode": "test"}

    if not hs256_secret:
        raise SecurityError("JWT_HS256_SECRET is required for strict validation")

    try:
        payload = jwt.decode(
            token,
            hs256_secret,
            algorithms=["HS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
        return payload
    except InvalidTokenError as exc:
        raise SecurityError(f"Invalid JWT token: {exc}") from exc
