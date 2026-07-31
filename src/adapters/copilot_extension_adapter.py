from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.utils.schemas import CopilotRiskResponse


class CopilotExtensionAdapter:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode

    def to_copilot_security(self, report: dict[str, Any]) -> dict[str, Any]:
        risk_score = float(report.get("risk_score", 0.0))
        severity = report.get("severity", "medium")

        payload = CopilotRiskResponse(
            metadata={
                "source": "vrtx-sentinel-azure",
                "adapter_version": "1.0.0",
                "generated_at": datetime.now(UTC).isoformat(),
                "mode": "test" if self.test_mode else "production",
                "report_id": report.get("id", str(uuid4())),
            },
            risk={
                "severity": severity,
                "risk_score": risk_score,
                "summary": report.get("summary", "N/A"),
            },
            evidence=[
                {"type": "indicator", "detail": ev}
                for ev in report.get("evidence", [])
            ],
            recommendation=report.get("recommendation", "Investigate and contain."),
            actionable_steps=report.get(
                "actionable_steps",
                [
                    "Isolar identidades o endpoints comprometidos",
                    "Rotar secretos en Azure Key Vault",
                    "Aumentar telemetria y retencion para caza de amenazas",
                ],
            ),
        )
        return payload.to_dict()


def build_http_response(report: dict[str, Any], test_mode: bool = False) -> dict[str, Any]:
    adapter = CopilotExtensionAdapter(test_mode=test_mode)
    return adapter.to_copilot_security(report)
