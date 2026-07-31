from __future__ import annotations

import json

import azure.functions as func

from src.clients.eventgrid_client import VrtxEventGridPublisher
from src.utils.config import load_settings
from src.utils.idempotency import cache_response, get_cached_response
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.rate_limiter import allow_request, build_rate_limit_key
from src.utils.schemas import validate_report_payload
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

    try:
        report = validate_report_payload(req.get_json() if req.get_body() else {})
    except ValueError as exc:
        log_with_context(logger, "Invalid request payload", error=str(exc))
        return secure_json_response({"error": str(exc)}, 400, settings.security_csp, origin=origin)

    idempotency_key = req.headers.get("Idempotency-Key") or report["id"]
    cached = get_cached_response("publish_event", idempotency_key, settings.idempotency_ttl_seconds)
    if cached is not None:
        return secure_json_response(
            cached,
            200,
            settings.security_csp,
            origin=origin,
            extra_headers={"X-Idempotent-Replay": "true"},
        )

    publisher = VrtxEventGridPublisher(
        topic_endpoint=settings.eventgrid_topic_endpoint,
        keyvault_uri=settings.keyvault_uri,
        topic_key_secret_name=settings.eventgrid_topic_key_secret_name,
    )
    payload = publisher.publish_risk_event(report)
    response_payload = {"published": True, "event": payload}
    cache_response("publish_event", idempotency_key, response_payload)

    return secure_json_response(response_payload, 200, settings.security_csp, origin=origin)
