from __future__ import annotations

import json

import azure.functions as func

from src.adapters.copilot_extension_adapter import build_http_response
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.security import SecurityError, extract_bearer_token, validate_jwt_token

logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    settings = load_settings()
    test_mode = req.params.get("test_mode", "false").lower() == "true"

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
        return func.HttpResponse(str(exc), status_code=401)

    report = req.get_json() if req.get_body() else {}
    copilot_payload = build_http_response(report, test_mode=test_mode)

    log_with_context(logger, "Copilot adapter response generated", report_id=copilot_payload["metadata"]["report_id"])
    return func.HttpResponse(json.dumps(copilot_payload, ensure_ascii=True), status_code=200, mimetype="application/json")
