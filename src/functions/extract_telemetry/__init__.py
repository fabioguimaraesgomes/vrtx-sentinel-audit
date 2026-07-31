from __future__ import annotations

import json
from pathlib import Path

import azure.functions as func

from src.clients.adx_client import ADXClient
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context
from src.utils.security import SecurityError, extract_bearer_token, validate_jwt_token

logger = get_logger(__name__)
KQL_PATH = Path(__file__).resolve().parents[3] / "kql" / "telemetry_window.kql"


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
    window_minutes = int(body.get("window_minutes", 30))

    query = KQL_PATH.read_text(encoding="utf-8")
    query = query.replace("window_minutes:int = 30", f"window_minutes:int = {window_minutes}")

    client = ADXClient(
        cluster_uri=settings.adx_cluster_uri,
        database=settings.adx_database,
        managed_identity_client_id=settings.adx_managed_identity_client_id,
        keyvault_uri=settings.keyvault_uri,
        app_id_secret_name=settings.keyvault_adx_app_id_secret_name,
        app_key_secret_name=settings.keyvault_adx_app_key_secret_name,
    )
    rows = client.query(query)

    response = {"count": len(rows), "telemetry": rows}
    log_with_context(logger, "Telemetry extracted", count=len(rows))
    return func.HttpResponse(json.dumps(response, ensure_ascii=True), status_code=200, mimetype="application/json")
