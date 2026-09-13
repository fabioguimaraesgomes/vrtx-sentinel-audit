"""Borrador determinista de Report a partir de findings y score.

Sin LLM obligatorio. Si LLM_PROVIDER=xai y hay XAI_API_KEY, el adaptador
opcional puede reescribir solo el resumen ejecutivo.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.models import Finding, Report, Score

# Remediaciones por codigo de regla (ES / EN).
REMEDIATIONS: dict[str, dict[str, str]] = {
    "VRTX-STORAGE-PUBLIC": {
        "es": (
            "Restringir ACL/IAM del bucket: eliminar allUsers/allAuthenticatedUsers, "
            "activar publicAccessPrevention=enforced y revisar URLs firmadas."
        ),
        "en": (
            "Restrict bucket ACL/IAM: remove allUsers/allAuthenticatedUsers, "
            "set publicAccessPrevention=enforced, and review signed URLs."
        ),
    },
    "VRTX-IAM-OWNER": {
        "es": (
            "Retirar roles/owner de usuarios cotidianos; usar cuentas de "
            "break-glass y privilegios temporales con aprobacion."
        ),
        "en": (
            "Remove roles/owner from day-to-day users; use break-glass accounts "
            "and time-bound privileged access with approval."
        ),
    },
    "VRTX-IAM-PRIMITIVE": {
        "es": (
            "Sustituir roles primitivos (editor/viewer) por roles predefinidos "
            "o personalizados con minimo privilegio."
        ),
        "en": (
            "Replace primitive roles (editor/viewer) with predefined or custom "
            "roles following least privilege."
        ),
    },
    "VRTX-NET-EXTERNAL-IP": {
        "es": (
            "Confirmar si la IP publica es necesaria; preferir Load Balancer, "
            "Cloud NAT o IAP y limitar firewall de entrada."
        ),
        "en": (
            "Confirm whether the public IP is required; prefer Load Balancer, "
            "Cloud NAT or IAP and tighten ingress firewall rules."
        ),
    },
    "VRTX-AUTH-FAILED-BURST": {
        "es": (
            "Investigar origen de fallos de autenticacion: rate-limit, MFA, "
            "bloqueo temporal y revision de credenciales comprometidas."
        ),
        "en": (
            "Investigate authentication failure source: rate-limit, MFA, "
            "temporary lockout, and review for compromised credentials."
        ),
    },
    "VRTX-INGEST-OK": {
        "es": "Sin accion de remediacion; mantener monitorizacion periodica.",
        "en": "No remediation action; keep periodic monitoring.",
    },
}

_DEFAULT_REMEDIATION = {
    "es": "Revisar el hallazgo, priorizar por severidad y documentar el plan de correccion.",
    "en": "Review the finding, prioritize by severity, and document the remediation plan.",
}


def draft_report(
    findings: list[Finding],
    score: Score,
    *,
    lang: str = "es",
    client_id: str | None = None,
) -> Report:
    """Genera un Report determinista (titulo, score/grado, findings, remediaciones).

    No requiere LLM. El resumen ejecutivo puede enriquecerse despues via
    services.xai_adapter.maybe_rewrite_summary si el entorno lo habilita.
    """
    lang_key = (lang or "es").strip().lower()
    if lang_key not in ("es", "en"):
        lang_key = "es"

    safe_findings = [f for f in (findings or []) if f is not None]
    if score is None:
        from services.score import score_findings as _score_findings
        score = _score_findings(safe_findings)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_id = f"rpt-{uuid.uuid4().hex[:12]}"
    request_id = client_id or "local-mvp"

    title = _title(score, lang_key, client_id)
    remediations = _remediations_for(safe_findings, lang_key)
    summary = _executive_summary(safe_findings, score, remediations, lang_key)

    report = Report(
        report_id=report_id,
        generated_at=now,
        request_id=request_id,
        score=score,
        findings=list(safe_findings),
        summary=summary,
        title=title,
        client_id=client_id,
        lang=lang_key,
        remediations=remediations,
    )

    # Adaptador opcional: solo reescribe summary si LLM_PROVIDER=xai + key.
    try:
        from services.xai_adapter import maybe_rewrite_summary

        maybe_rewrite_summary(report)
    except Exception:
        # Nunca fallar el borrador determinista por el adaptador.
        pass

    return report


def _title(score: Score, lang: str, client_id: str | None) -> str:
    client = client_id or ("local" if lang == "es" else "local")
    grade = (score.grade if score and score.grade else "A")
    total = float(score.total) if score and score.total is not None else 0.0
    if lang == "en":
        return (
            f"VRTX Sentinel draft report - grade {grade} "
            f"(score {total:g}) - {client}"
        )
    return (
        f"Borrador de informe VRTX Sentinel - grado {grade} "
        f"(puntuacion {total:g}) - {client}"
    )


def _remediations_for(findings: list[Finding] | None, lang: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for finding in findings or []:
        if finding is None:
            continue
        code = finding.rule_id or "UNKNOWN"
        # Una remediacion por codigo + finding_id para trazabilidad.
        key = f"{code}|{finding.finding_id}"
        if key in seen:
            continue
        seen.add(key)
        catalog = REMEDIATIONS.get(code, _DEFAULT_REMEDIATION)
        suggestion = catalog.get(lang) or catalog.get("es") or _DEFAULT_REMEDIATION["es"]
        items.append(
            {
                "finding_id": finding.finding_id,
                "code": code,
                "severity": finding.severity,
                "suggestion": suggestion,
            }
        )
    return items


def _executive_summary(
    findings: list[Finding] | None,
    score: Score,
    remediations: list[dict[str, Any]],
    lang: str,
) -> str:
    safe = [f for f in (findings or []) if f is not None]
    security = [f for f in safe if (f.severity or "").lower() != "info"]
    by_sev = (score.by_severity if score else None) or {}
    codes = sorted({f.rule_id for f in safe if f.rule_id})
    grade = (score.grade if score and score.grade else "A")
    total = float(score.total) if score and score.total is not None else 0.0
    findings_count = (
        score.findings_count if score and score.findings_count is not None else len(safe)
    )

    if lang == "en":
        lines = [
            f"Draft security report. Grade {grade}, weighted score {total:g}.",
            f"Findings: {findings_count} total "
            f"({len(security)} security-relevant).",
            (
                "By severity - critical={c}, high={h}, medium={m}, low={l}, info={i}."
            ).format(
                c=by_sev.get("critical", 0),
                h=by_sev.get("high", 0),
                m=by_sev.get("medium", 0),
                l=by_sev.get("low", 0),
                i=by_sev.get("info", 0),
            ),
        ]
        if codes:
            lines.append("Rule codes: " + ", ".join(codes) + ".")
        if remediations:
            lines.append(
                f"{len(remediations)} remediation suggestion(s) attached per finding code."
            )
        lines.append(
            "This summary is deterministic; optional xAI may polish wording only."
        )
        return " ".join(lines)

    lines = [
        f"Borrador de informe de seguridad. Grado {grade}, "
        f"puntuacion ponderada {total:g}.",
        f"Hallazgos: {findings_count} en total "
        f"({len(security)} con relevancia de seguridad).",
        (
            "Por severidad - critical={c}, high={h}, medium={m}, low={l}, info={i}."
        ).format(
            c=by_sev.get("critical", 0),
            h=by_sev.get("high", 0),
            m=by_sev.get("medium", 0),
            l=by_sev.get("low", 0),
            i=by_sev.get("info", 0),
        ),
    ]
    if codes:
        lines.append("Codigos de regla: " + ", ".join(codes) + ".")
    if remediations:
        lines.append(
            f"{len(remediations)} sugerencia(s) de remediacion por codigo de hallazgo."
        )
    lines.append(
        "Este resumen es determinista; xAI opcional solo puede pulir la redaccion."
    )
    return " ".join(lines)
