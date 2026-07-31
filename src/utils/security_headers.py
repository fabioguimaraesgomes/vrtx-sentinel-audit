from __future__ import annotations

import json
from typing import Any

import azure.functions as func


def is_origin_allowed(origin: str | None, allowed_origins: list[str]) -> bool:
    if not origin:
        return True
    if not allowed_origins:
        return False
    return origin in allowed_origins


def _base_headers(csp: str, origin: str | None = None) -> dict[str, str]:
    headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": csp,
    }
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
    return headers


def secure_json_response(
    payload: dict[str, Any],
    status_code: int,
    csp: str,
    origin: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> func.HttpResponse:
    headers = _base_headers(csp, origin)
    if extra_headers:
        headers.update(extra_headers)
    return func.HttpResponse(
        body=json.dumps(payload, ensure_ascii=True),
        status_code=status_code,
        mimetype="application/json",
        headers=headers,
    )


def secure_text_response(
    text: str,
    status_code: int,
    csp: str,
    origin: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> func.HttpResponse:
    headers = _base_headers(csp, origin)
    if extra_headers:
        headers.update(extra_headers)
    return func.HttpResponse(body=text, status_code=status_code, headers=headers)
