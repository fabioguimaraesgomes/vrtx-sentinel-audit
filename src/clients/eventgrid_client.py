from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from azure.eventgrid import EventGridEvent, EventGridPublisherClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.credentials import AzureKeyCredential

from src.utils.logging_utils import get_logger, log_with_context

logger = get_logger(__name__)


class VrtxEventGridPublisher:
    def __init__(
        self,
        topic_endpoint: str,
        keyvault_uri: str | None = None,
        topic_key_secret_name: str | None = None,
    ) -> None:
        if keyvault_uri and topic_key_secret_name:
            credential = DefaultAzureCredential()
            secret_client = SecretClient(vault_url=keyvault_uri, credential=credential)
            topic_key = secret_client.get_secret(topic_key_secret_name).value
            auth_credential = AzureKeyCredential(topic_key)
            auth_mode = "keyvault-topic-key"
        else:
            auth_credential = DefaultAzureCredential()
            auth_mode = "managed-identity"

        self.client = EventGridPublisherClient(topic_endpoint, auth_credential)
        log_with_context(logger, "Event Grid publisher initialized", auth_mode=auth_mode)

    def publish_risk_event(self, report: dict[str, Any]) -> dict[str, Any]:
        event_payload = {
            "id": report.get("id", str(uuid4())),
            "timestamp": report.get("timestamp", datetime.now(UTC).isoformat()),
            "severity": report.get("severity", "medium"),
            "risk_score": report.get("risk_score", 0.5),
            "summary": report.get("summary", "N/A"),
            "evidence": report.get("evidence", []),
            "recommendation": report.get("recommendation", "N/A"),
        }
        event = EventGridEvent(
            subject="vrtx/sentinel/risk",
            event_type="VrtxSentinel.RiskDetected",
            data_version="1.0",
            data=event_payload,
        )
        self.client.send([event])
        log_with_context(logger, "Event Grid event published", event_id=event_payload["id"])
        return event_payload
