from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class RiskEvent:
    id: str
    severity: str
    risk_score: float
    summary: str
    evidence: list[str]
    recommendation: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def validate(self) -> None:
        if not (0.0 <= self.risk_score <= 1.0):
            raise ValueError("risk_score must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class CopilotRiskResponse:
    metadata: dict[str, Any]
    risk: dict[str, Any]
    evidence: list[dict[str, Any]]
    recommendation: str
    actionable_steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_report_payload(report: dict[str, Any]) -> dict[str, Any]:
    required_fields = ("id", "severity", "risk_score", "summary", "evidence", "recommendation")
    missing = [field for field in required_fields if field not in report]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(report["id"], str) or not report["id"].strip():
        raise ValueError("id must be a non-empty string")
    if not isinstance(report["severity"], str) or not report["severity"].strip():
        raise ValueError("severity must be a non-empty string")

    try:
        risk_score = float(report["risk_score"])
    except (TypeError, ValueError) as exc:
        raise ValueError("risk_score must be a number between 0.0 and 1.0") from exc
    if not (0.0 <= risk_score <= 1.0):
        raise ValueError("risk_score must be between 0.0 and 1.0")

    if not isinstance(report["summary"], str) or not report["summary"].strip():
        raise ValueError("summary must be a non-empty string")
    if not isinstance(report["recommendation"], str) or not report["recommendation"].strip():
        raise ValueError("recommendation must be a non-empty string")

    evidence = report["evidence"]
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        raise ValueError("evidence must be a list of strings")

    actionable_steps = report.get("actionable_steps", [])
    if not isinstance(actionable_steps, list) or any(not isinstance(item, str) for item in actionable_steps):
        raise ValueError("actionable_steps must be a list of strings")

    return {
        "id": report["id"].strip(),
        "severity": report["severity"].strip(),
        "risk_score": risk_score,
        "summary": report["summary"].strip(),
        "evidence": evidence,
        "recommendation": report["recommendation"].strip(),
        "actionable_steps": actionable_steps,
    }
