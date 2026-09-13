"""Ingesta file-first: JSON/CSV -> list[Evidence]. No requiere BigQuery."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.models import Evidence

SUPPORTED_SUFFIXES = {".json", ".csv"}
_COLLECTION_KEYS = ("items", "records", "data", "evidences", "rows")


def ingest_file(path: str | Path) -> list[Evidence]:
    """Lee un .json (objeto o lista) o .csv y normaliza a Evidence."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"No existe el fichero: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Formato no soportado: {suffix}. Use .json o .csv"
        )

    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source = str(file_path)

    if suffix == ".json":
        items = _load_json_items(file_path)
    else:
        items = _load_csv_items(file_path)

    return [_normalize(item, source, ingested_at, file_path) for item in items]


def _load_json_items(file_path: Path) -> list[Any]:
    raw = json.loads(file_path.read_text(encoding="utf-8-sig"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in _COLLECTION_KEYS:
            value = raw.get(key)
            if isinstance(value, list):
                return value
        return [raw]
    return [{"value": raw}]


def _load_csv_items(file_path: Path) -> list[dict[str, Any]]:
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    return rows if rows else [{}]


def _infer_kind(payload: dict[str, Any], file_path: Path) -> str:
    explicit = payload.get("kind")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()

    name = file_path.name.lower()
    if "iam" in name or "binding" in name:
        return "iam"
    if any(token in name for token in ("bucket", "storage", "gcs")):
        return "storage"
    if any(token in name for token in ("vpc", "flow", "network")):
        return "vpc"

    keys = {str(key).lower() for key in payload}
    if keys & {"role", "roles", "bindings", "members"}:
        return "iam"
    if keys & {"bucket", "buckets", "acl"}:
        return "storage"
    if keys & {"external_ip", "public_ip", "source_ip", "dest_ip"}:
        return "vpc"
    return "generic"


def _normalize(
    item: Any,
    source: str,
    ingested_at: str,
    file_path: Path,
) -> Evidence:
    if isinstance(item, dict):
        payload = dict(item)
    else:
        payload = {"value": item}
    kind = _infer_kind(payload, file_path)
    return Evidence(
        kind=kind,
        source=source,
        payload=payload,
        ingested_at=ingested_at,
    )
