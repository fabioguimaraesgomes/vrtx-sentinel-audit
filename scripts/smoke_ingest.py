"""Smoke local: ingest -> checks -> score -> draft_report sobre mocks/fixtures/sample_iam.json."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Smoke determinista: sin llamadas LLM.
os.environ.setdefault("LLM_PROVIDER", "off")

from services.checks_basic import run_checks
from services.ingest import ingest_file
from services.models import to_dict
from services.report import draft_report
from services.score import score_findings

FIXTURE = ROOT / "mocks" / "fixtures" / "sample_iam.json"

SAMPLE_IAM = [
    {
        "kind": "iam",
        "project": "gen-lang-client-0320924150",
        "bindings": [
            {
                "role": "roles/owner",
                "members": ["user:admin@example.com"],
            },
            {
                "role": "roles/editor",
                "members": ["user:dev@example.com"],
            },
            {
                "role": "roles/iam.securityAdmin",
                "members": ["user:sec@example.com"],
            },
        ],
    },
    {
        "kind": "storage",
        "bucket": "vrtx-public-assets",
        "public": True,
        "acl": ["allUsers"],
    },
    {
        "kind": "vpc",
        "instance": "web-1",
        "external_ip": "203.0.113.10",
        "internal_ip": "10.0.0.8",
    },
]


def ensure_fixture() -> Path:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    if not FIXTURE.exists():
        FIXTURE.write_text(
            json.dumps(SAMPLE_IAM, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return FIXTURE


def main() -> int:
    path = ensure_fixture()
    evidences = ingest_file(path)
    findings = run_checks(evidences)
    score = score_findings(findings)
    report = draft_report(findings, score, lang="es", client_id="smoke-local")

    # Contrato del fixture sample_iam: score ponderado = 27 (LLM off).
    expected_score = 27.0
    if score.total != expected_score:
        raise AssertionError(
            f"score.total esperado {expected_score}, obtenido {score.total}"
        )

    print(f"report_title: {report.title}")
    print(f"report_findings: {len(report.findings)}")
    summary = {
        "ok": True,
        "mvp": "file-ingest",
        "source": str(path),
        "evidences": len(evidences),
        "findings_count": len(findings),
        "score": to_dict(score),
        "report": {
            "title": report.title,
            "findings_count": len(report.findings),
            "lang": report.lang,
            "summary": report.summary,
            "remediations": len(report.remediations),
        },
        "findings": [to_dict(item) for item in findings],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
