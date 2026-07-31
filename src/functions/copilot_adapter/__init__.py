from __future__ import annotations

import json

import azure.functions as func

from src.adapters.copilot_extension_adapter import build_http_response
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.rate_limiter import allow_request, build_rate_limit_key
from src.utils.schemas import validate_report_payload
from src.utils.security_headers import is_origin_allowed, secure_json_response, secure_text_response
from src.utils.security import SecurityError, extract_bearer_token, validate_jwt_token

logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    settings = load_settings()
    test_mode = req.params.get("test_mode", "false").lower() == "true"
    origin = req.headers.get("Origin")

    if not is_origin_allowed(origin, settings.cors_allowed_origins):
        return secure_json_response({"error": "Origin not allowed"}, 403, settings.security_csp)

    rate_key = build_rate_limit_key(req.headers.get("Authorization"), fallback=req.url)
    if not allow_request(rate_key, settings.rate_limit_per_minute):
        return secure_json_response({"error": "Rate limit exceeded"}, 429, settings.security_csp, origin=origin)

    try:
        token = extract_bearer_token(dict(req.headers))
        validate_jwt_token(
            token,
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            hs256_secret=settings.jwt_hs256_secret,
            allow_test_mode=test_mode,
        )
    except SecurityError as exc:
        log_with_context(logger, "Unauthorized access", error=str(exc), test_mode=test_mode)
        return secure_text_response(str(exc), 401, settings.security_csp, origin=origin)

    try:
        raw_report = req.get_json() if req.get_body() else {}
        report = validate_report_payload(raw_report)
        copilot_payload = build_http_response(report, test_mode=test_mode)
    except ValueError as exc:
        log_with_context(logger, "Invalid request payload", error=str(exc), test_mode=test_mode)
        return secure_json_response({"error": str(exc)}, 400, settings.security_csp, origin=origin)
    except Exception as exc:
        log_with_context(logger, "Copilot adapter failed", error=str(exc), test_mode=test_mode)
        return secure_json_response({"error": str(exc)}, 500, settings.security_csp, origin=origin)

    log_with_context(logger, "Copilot adapter response generated", report_id=copilot_payload["metadata"]["report_id"])
    return secure_json_response(copilot_payload, 200, settings.security_csp, origin=origin)
