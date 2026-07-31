from __future__ import annotations

import json

import azure.functions as func

from src.adapters.risk_inference import run_risk_inference
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.rate_limiter import allow_request, build_rate_limit_key
from src.utils.security_headers import is_origin_allowed, secure_json_response, secure_text_response
from src.utils.security import SecurityError, extract_bearer_token, validate_jwt_token

logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    settings = load_settings()
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
        )
    except SecurityError as exc:
        log_with_context(logger, "Unauthorized access", error=str(exc))
        return secure_text_response(str(exc), 401, settings.security_csp, origin=origin)

    body = req.get_json() if req.get_body() else {}
    events = body.get("telemetry", [])
    report = run_risk_inference(events)

    log_with_context(logger, "Inference completed", risk_score=report.get("risk_score"))
    return secure_json_response(report, 200, settings.security_csp, origin=origin)
