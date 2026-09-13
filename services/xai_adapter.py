"""Adaptador opcional xAI (Grok) para pulir el resumen ejecutivo.

Solo activo si LLM_PROVIDER=xai y XAI_API_KEY esta definido.
Reescribe unicamente Report.summary; nunca inventa findings ni cambia score.
Por defecto LLM_PROVIDER=off -> no-op.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from services.models import Report

XAI_BASE = "https://api.x.ai/v1"
XAI_MODEL = "grok-4.6"
DEFAULT_PROVIDER = "off"


def maybe_rewrite_summary(report: Report) -> Report:
    """Si el proveedor xAI esta habilitado, reescribe solo summary in-place."""
    provider = (os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    api_key = (os.environ.get("XAI_API_KEY") or "").strip()

    if provider != "xai" or not api_key:
        return report

    rewritten = _call_xai_summary(report, api_key)
    if rewritten:
        report.summary = rewritten
    return report


def _call_xai_summary(report: Report, api_key: str) -> str | None:
    """Llama a grok-4.6 para reescribir el resumen; fallos -> None (silencioso)."""
    finding_titles = [
        {
            "code": f.rule_id,
            "severity": f.severity,
            "title": f.title,
        }
        for f in (report.findings or [])
    ]
    lang = report.lang or "es"
    system = (
        "You rewrite executive summaries for security audit draft reports. "
        "Rules: (1) Do NOT invent findings, scores, grades, IPs, roles, or "
        "remediations. (2) Only rephrase the provided summary using the listed "
        "finding titles/codes as context. (3) Keep the same language as the "
        f"input (lang={lang}). (4) Return plain text only, no markdown fences."
    )
    user_payload = {
        "lang": lang,
        "title": report.title,
        "grade": report.score.grade if report.score else None,
        "score_total": report.score.total if report.score else None,
        "findings": finding_titles,
        "current_summary": report.summary,
    }
    body: dict[str, Any] = {
        "model": XAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    "Rewrite this executive summary only. Do not add findings.\n"
                    + json.dumps(user_payload, ensure_ascii=False)
                ),
            },
        ],
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        f"{XAI_BASE}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        choices = data.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        return content or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        return None
