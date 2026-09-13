"""Puntuacion simple por recuento ponderado de findings."""
from __future__ import annotations

from collections import Counter

from services.models import Finding, Score

WEIGHTS: dict[str, float] = {
    "critical": 10.0,
    "high": 5.0,
    "medium": 2.0,
    "low": 1.0,
    "info": 0.0,
}


def score_findings(findings: list[Finding] | None) -> Score:
    """Suma pesos por severidad y asigna un grado A-F (A = sin riesgo)."""
    safe = [f for f in (findings or []) if f is not None]
    counts: Counter[str] = Counter()
    total = 0.0
    for finding in safe:
        severity = (finding.severity or "info").strip().lower()
        if severity not in WEIGHTS:
            severity = "info"
        counts[severity] += 1
        total += WEIGHTS[severity]

    by_severity = {key: int(counts.get(key, 0)) for key in WEIGHTS}
    return Score(
        total=total,
        grade=_grade(total),
        findings_count=len(safe),
        by_severity=by_severity,
        weights=dict(WEIGHTS),
    )


def _grade(total: float) -> str:
    if total <= 0:
        return "A"
    if total < 5:
        return "B"
    if total < 10:
        return "C"
    if total < 20:
        return "D"
    return "F"
