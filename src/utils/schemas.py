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
