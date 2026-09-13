"""Modelos de dominio JSON-serializables (MVP file-first).

Cadena: AuditRequest -> Evidence -> Finding -> Score -> Report / Alert.
Sin secretos. Identificadores en ingles; comentarios en espanol OK.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, TypedDict


class AuditRequestDict(TypedDict, total=False):
    request_id: str
    customer: str
    source: str
    requested_at: str
    notes: str
    metadata: dict[str, Any]


class EvidenceDict(TypedDict):
    kind: str
    source: str
    payload: dict[str, Any]
    ingested_at: str


class FindingDict(TypedDict, total=False):
    finding_id: str
    severity: str
    title: str
    description: str
    evidence_source: str
    rule_id: str
    metadata: dict[str, Any]


class ScoreDict(TypedDict, total=False):
    total: float
    grade: str
    findings_count: int
    by_severity: dict[str, int]
    weights: dict[str, float]


class ReportDict(TypedDict, total=False):
    report_id: str
    generated_at: str
    request_id: str
    score: ScoreDict
    findings: list[FindingDict]
    summary: str


class AlertDict(TypedDict, total=False):
    alert_id: str
    severity: str
    title: str
    message: str
    created_at: str
    finding_ids: list[str]


@dataclass
class AuditRequest:
    request_id: str
    customer: str
    source: str
    requested_at: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    kind: str
    source: str
    payload: dict[str, Any]
    ingested_at: str


@dataclass
class Finding:
    finding_id: str
    severity: str
    title: str
    description: str
    evidence_source: str
    rule_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Score:
    total: float
    grade: str
    findings_count: int
    by_severity: dict[str, int] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


@dataclass
class Report:
    report_id: str
    generated_at: str
    request_id: str
    score: Score
    findings: list[Finding] = field(default_factory=list)
    summary: str = ""


@dataclass
class Alert:
    alert_id: str
    severity: str
    title: str
    message: str
    created_at: str
    finding_ids: list[str] = field(default_factory=list)


def to_dict(obj: Any) -> dict[str, Any]:
    """Convierte un dataclass de dominio a dict serializable."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"to_dict espera un dataclass, recibio {type(obj)!r}")


def to_json(obj: Any, *, indent: int | None = 2) -> str:
    """Serializa un dataclass de dominio a JSON UTF-8."""
    return json.dumps(to_dict(obj), ensure_ascii=False, default=str, indent=indent)
