from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.clients.openai_client import AzureOpenAIRiskClient
from src.utils.config import load_settings
from src.utils.logging_utils import get_logger, log_with_context

logger = get_logger(__name__)
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "risk_prompt.txt"


def _temporal_concentration(events: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = Counter()
    for item in events:
        ts_raw = item.get("timestamp")
        if not ts_raw:
            continue
        ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        bucket = ts.strftime("%Y-%m-%dT%H:%M")
        buckets[bucket] += 1

    if not buckets:
        return {"peak_minute": None, "peak_count": 0}
    peak_minute, peak_count = buckets.most_common(1)[0]
    return {"peak_minute": peak_minute, "peak_count": peak_count}


def _triangulate_deviations(events: list[dict[str, Any]]) -> dict[str, Any]:
    zscore_hits = sum(1 for e in events if float(e.get("metric_zscore", 0)) >= 2.5)
    geo_drift_hits = sum(1 for e in events if bool(e.get("unexpected_geo")))
    device_drift_hits = sum(1 for e in events if bool(e.get("device_fingerprint_mismatch")))
    return {
        "zscore_hits": zscore_hits,
        "geo_drift_hits": geo_drift_hits,
        "device_drift_hits": device_drift_hits,
    }


def _detect_suspicious_patterns(events: list[dict[str, Any]]) -> list[str]:
    patterns: list[str] = []
    source_ips = [str(e.get("source_ip")) for e in events if e.get("source_ip")]
    ip_counts = Counter(source_ips)
    repeated = [ip for ip, count in ip_counts.items() if count >= 5]
    if repeated:
        patterns.append(f"IPs repetidas con alta frecuencia: {', '.join(repeated[:5])}")

    failed_auth = sum(1 for e in events if str(e.get("event_type", "")).lower() == "failed_auth")
    if failed_auth >= 3:
        patterns.append(f"Concentracion de fallos de autenticacion: {failed_auth}")

    if not patterns:
        patterns.append("No se detectaron patrones sospechosos fuertes")
    return patterns


def run_risk_inference(telemetry_events: list[dict[str, Any]]) -> dict[str, Any]:
    settings = load_settings()

    temporal = _temporal_concentration(telemetry_events)
    deviations = _triangulate_deviations(telemetry_events)
    patterns = _detect_suspicious_patterns(telemetry_events)

    local_score = min(
        1.0,
        (deviations["zscore_hits"] * 0.12)
        + (deviations["geo_drift_hits"] * 0.15)
        + (deviations["device_drift_hits"] * 0.15)
        + (temporal["peak_count"] * 0.03),
    )

    with PROMPT_PATH.open("r", encoding="utf-8") as f:
        prompt = f.read()

    ai_client = AzureOpenAIRiskClient(
        endpoint=settings.openai_endpoint,
        deployment=settings.openai_deployment,
        api_version=settings.openai_api_version,
        keyvault_uri=settings.keyvault_uri,
        api_key_secret_name=settings.openai_key_secret_name,
    )

    model_output = ai_client.infer_risk(
        prompt=prompt,
        telemetry={
            "events": telemetry_events,
            "triangulation": deviations,
            "temporal_concentration": temporal,
            "suspicious_patterns": patterns,
            "local_risk_score": local_score,
        },
    )

    if "risk_score" not in model_output:
        model_output["risk_score"] = local_score
    if "severity" not in model_output:
        model_output["severity"] = "high" if local_score >= 0.75 else "medium"

    model_output["triangulation"] = deviations
    model_output["temporal_concentration"] = temporal
    model_output["suspicious_patterns"] = patterns

    log_with_context(
        logger,
        "Risk inference assembled",
        local_risk_score=local_score,
        final_risk_score=model_output.get("risk_score"),
    )
    return model_output
