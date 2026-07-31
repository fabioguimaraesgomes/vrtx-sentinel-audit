from __future__ import annotations

import json

import azure.functions as func

from src.adapters.risk_inference import run_risk_inference
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

    body = req.get_json() if req.get_body() else {}
    events = body.get("telemetry", [])
    report = run_risk_inference(events)

    log_with_context(logger, "Inference completed", risk_score=report.get("risk_score"))
    return func.HttpResponse(json.dumps(report, ensure_ascii=True), status_code=200, mimetype="application/json")
