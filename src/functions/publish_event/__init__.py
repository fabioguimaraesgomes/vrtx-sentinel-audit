from __future__ import annotations

import json

import azure.functions as func

from src.clients.eventgrid_client import VrtxEventGridPublisher
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.security import SecurityError, extract_bearer_token, validate_jwt_token

logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    settings = load_settings()

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
        return func.HttpResponse(str(exc), status_code=401)

    report = req.get_json() if req.get_body() else {}

    publisher = VrtxEventGridPublisher(
        topic_endpoint=settings.eventgrid_topic_endpoint,
        keyvault_uri=settings.keyvault_uri,
        topic_key_secret_name=settings.eventgrid_topic_key_secret_name,
    )
    payload = publisher.publish_risk_event(report)

    return func.HttpResponse(json.dumps({"published": True, "event": payload}, ensure_ascii=True), status_code=200, mimetype="application/json")
