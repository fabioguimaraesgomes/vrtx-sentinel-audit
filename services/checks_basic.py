"""Checks deterministas sobre Evidence (IAM, storage publico, IPs externas)."""
from __future__ import annotations

import hashlib
import ipaddress
import re
from typing import Any, Iterator

from services.models import Evidence, Finding

PRIMITIVE_ROLES = {
    "roles/owner": "critical",
    "roles/editor": "high",
    "roles/viewer": "medium",
    "owner": "critical",
    "editor": "high",
    "viewer": "medium",
}
OWNER_ROLES = {"roles/owner", "owner"}
PUBLIC_PRINCIPALS = {"allusers", "allauthenticatedusers"}
IP_KEY_HINTS = (
    "ip",
    "external_ip",
    "public_ip",
    "source_ip",
    "dest_ip",
    "destination_ip",
    "client_ip",
    "remote_ip",
    "nat_ip",
    "address",
    "sourceaddress",
    "destaddress",
    "ipaddress",
)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def run_checks(evidences: list[Evidence] | None) -> list[Finding]:
    """Heuristicas deterministas; si no hay senales, Finding informativo."""
    findings: list[Finding] = []
    for evidence in evidences or []:
        if evidence is None:
            continue
        # None-safety: payload debe ser dict para los checkers.
        if not isinstance(getattr(evidence, "payload", None), dict):
            evidence.payload = {}
        findings.extend(_check_public_buckets(evidence))
        findings.extend(_check_iam_roles(evidence))
        findings.extend(_check_external_ips(evidence))
        findings.extend(_check_failed_auth_burst(evidence))

    security = [item for item in findings if item.severity != "info"]
    if not security:
        findings.append(
            Finding(
                finding_id=_finding_id(
                    "VRTX-INGEST-OK",
                    "aggregate",
                    str(len(evidences)),
                ),
                severity="info",
                title="Datos ingeridos sin senales de riesgo",
                description=(
                    f"Se ingirieron {len(evidences)} evidencia(s). "
                    "No se detectaron buckets publicos, roles primitivos "
                    "ni IPs externas en el payload."
                ),
                evidence_source="aggregate",
                rule_id="VRTX-INGEST-OK",
                metadata={"evidences": len(evidences)},
            )
        )
    return findings


def _check_public_buckets(evidence: Evidence) -> list[Finding]:
    payload = evidence.payload if isinstance(evidence.payload, dict) else {}
    hits: list[str] = []

    public_flag = payload.get("public")
    if public_flag in (True, "true", "True", "yes", "1", 1):
        hits.append("public=true")

    acl = payload.get("acl") or payload.get("ACL")
    if isinstance(acl, list):
        for entry in acl:
            text = str(entry).lower()
            if any(marker in text for marker in PUBLIC_PRINCIPALS):
                hits.append(f"acl:{entry}")
    elif isinstance(acl, str) and any(
        marker in acl.lower() for marker in PUBLIC_PRINCIPALS
    ):
        hits.append(f"acl:{acl}")

    iam_cfg = payload.get("iamConfiguration") or payload.get("iam_configuration")
    if isinstance(iam_cfg, dict):
        raw_prev = iam_cfg.get("publicAccessPrevention")
        if raw_prev is None:
            raw_prev = iam_cfg.get("public_access_prevention")
        if raw_prev is not None:
            prevention = str(raw_prev).lower()
            if prevention not in {"enforced"}:
                hits.append(f"publicAccessPrevention={prevention or 'missing'}")

    for _path, value in _walk(payload):
        if isinstance(value, str) and value.lower() in PUBLIC_PRINCIPALS:
            hits.append(value)

    if not hits:
        return []

    unique = sorted(set(hits))
    extra = ",".join(unique)
    return [
        Finding(
            finding_id=_finding_id("VRTX-STORAGE-PUBLIC", evidence.source, extra),
            severity="critical",
            title="Posible bucket o recurso de almacenamiento publico",
            description=(
                "El payload indica acceso publico "
                f"({', '.join(unique)})."
            ),
            evidence_source=evidence.source,
            rule_id="VRTX-STORAGE-PUBLIC",
            metadata={"kind": evidence.kind, "signals": unique},
        )
    ]


def _check_iam_roles(evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()
    payload = evidence.payload if isinstance(evidence.payload, dict) else {}

    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        role = value.strip()
        role_l = role.lower()
        normalized = role if role.startswith("roles/") else role_l
        is_role_field = path.endswith("role") or path.endswith("roles")
        if normalized not in PRIMITIVE_ROLES and role not in PRIMITIVE_ROLES:
            continue
        if not is_role_field and not role.startswith("roles/"):
            continue

        key = role if role.startswith("roles/") else f"roles/{role_l}"
        if key in seen:
            continue
        seen.add(key)

        if key in OWNER_ROLES or role_l in OWNER_ROLES:
            findings.append(
                Finding(
                    finding_id=_finding_id(
                        "VRTX-IAM-OWNER", evidence.source, key
                    ),
                    severity="critical",
                    title="Asignacion de rol owner",
                    description=(
                        f"Se encontro el rol primitivo '{key}' en {path}."
                    ),
                    evidence_source=evidence.source,
                    rule_id="VRTX-IAM-OWNER",
                    metadata={"role": key, "path": path},
                )
            )
            continue

        severity = PRIMITIVE_ROLES.get(key) or PRIMITIVE_ROLES.get(role_l, "medium")
        findings.append(
            Finding(
                finding_id=_finding_id(
                    "VRTX-IAM-PRIMITIVE", evidence.source, key
                ),
                severity=severity,
                title="Rol primitivo IAM",
                description=(
                    f"Se encontro el rol primitivo '{key}' en {path}. "
                    "Prefiera roles predefinidos o personalizados."
                ),
                evidence_source=evidence.source,
                rule_id="VRTX-IAM-PRIMITIVE",
                metadata={"role": key, "path": path},
            )
        )
    return findings


def _check_external_ips(evidence: Evidence) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()
    payload = evidence.payload if isinstance(evidence.payload, dict) else {}

    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        leaf = path.rsplit(".", 1)[-1].lower()
        candidates: list[str] = []
        if leaf in IP_KEY_HINTS or leaf.endswith("_ip") or leaf.endswith("ip"):
            candidates.append(value.strip())
        else:
            candidates.extend(IPV4_RE.findall(value))

        for raw in candidates:
            parsed = _public_ip(raw)
            if parsed is None or parsed in seen:
                continue
            seen.add(parsed)
            findings.append(
                Finding(
                    finding_id=_finding_id(
                        "VRTX-NET-EXTERNAL-IP", evidence.source, parsed
                    ),
                    severity="medium",
                    title="Direccion IP externa expuesta",
                    description=(
                        f"IP publica '{parsed}' en {path}. "
                        "Revise si el alcance de red es intencional."
                    ),
                    evidence_source=evidence.source,
                    rule_id="VRTX-NET-EXTERNAL-IP",
                    metadata={"ip": parsed, "path": path},
                )
            )
    return findings



def _check_failed_auth_burst(evidence: Evidence) -> list[Finding]:
    """Si el payload parece logs de auth y failed_auth >= 3 -> finding."""
    if not _looks_like_auth_logs(evidence):
        return []

    count = _failed_auth_count(evidence.payload)
    if count < 3:
        return []

    severity = "high" if count >= 5 else "medium"
    return [
        Finding(
            finding_id=_finding_id(
                "VRTX-AUTH-FAILED-BURST", evidence.source, str(count)
            ),
            severity=severity,
            title="Rafaga de autenticaciones fallidas",
            description=(
                f"Se detectaron {count} intentos de autenticacion fallidos "
                "en evidencia de tipo auth/logs. Posible fuerza bruta o "
                "credenciales comprometidas."
            ),
            evidence_source=evidence.source,
            rule_id="VRTX-AUTH-FAILED-BURST",
            metadata={
                "kind": evidence.kind,
                "failed_auth": count,
                "threshold": 3,
            },
        )
    ]


def _looks_like_auth_logs(evidence: Evidence) -> bool:
    kind = (evidence.kind or "").strip().lower()
    if any(token in kind for token in ("auth", "login", "signin", "identity")):
        return True

    payload = evidence.payload if isinstance(evidence.payload, dict) else {}
    keys = {str(k).lower() for k in payload.keys()}
    auth_keys = {
        "failed_auth",
        "failed_logins",
        "auth_failures",
        "login_failures",
        "failed_attempts",
        "authentication_failures",
        "auth_events",
        "login_events",
        "sign_in_logs",
        "signin_logs",
    }
    if keys & auth_keys:
        return True

    for candidate_key in ("events", "logs", "records", "entries", "items"):
        rows = payload.get(candidate_key)
        if isinstance(rows, list) and rows:
            sample = rows[0] if isinstance(rows[0], dict) else {}
            sample_l = {str(k).lower(): v for k, v in sample.items()} if sample else {}
            if any(
                k in sample_l
                for k in (
                    "auth_result",
                    "login_result",
                    "status",
                    "event_type",
                    "result",
                )
            ):
                blob = " ".join(str(v).lower() for v in sample_l.values())
                if any(
                    marker in blob
                    for marker in ("fail", "denied", "invalid", "auth", "login")
                ):
                    return True
    return False


def _failed_auth_count(payload: dict[str, Any]) -> int:
    if not isinstance(payload, dict):
        return 0

    for key in (
        "failed_auth",
        "failed_logins",
        "auth_failures",
        "login_failures",
        "failed_attempts",
        "authentication_failures",
    ):
        if key in payload:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                pass

    total = 0
    for candidate_key in ("events", "logs", "records", "entries", "items"):
        rows = payload.get(candidate_key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if _row_is_failed_auth(row):
                total += 1
    return total


def _row_is_failed_auth(row: Any) -> bool:
    if isinstance(row, str):
        text = row.lower()
        return any(
            marker in text
            for marker in (
                "failed_auth",
                "auth failed",
                "login failed",
                "authentication failed",
                "invalid credentials",
            )
        )
    if not isinstance(row, dict):
        return False

    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in ("failed_auth", "auth_failed", "login_failed"):
        val = lowered.get(key)
        if val in (True, 1, "1", "true", "True", "yes"):
            return True

    for key in ("result", "status", "auth_result", "login_result", "outcome"):
        val = str(lowered.get(key, "")).lower()
        if val in {"fail", "failed", "failure", "denied", "error", "invalid"}:
            return True

    event_type = str(lowered.get("event_type", lowered.get("type", ""))).lower()
    if any(
        marker in event_type
        for marker in ("login_failed", "auth_failed", "signin_failed")
    ):
        return True

    blob = " ".join(str(v).lower() for v in lowered.values())
    return "authentication failed" in blob or "login failed" in blob


# RFC1918 / loopback / link-local / CGNAT. No usar is_private:
# en 3.14 rangos de documentacion (203.0.113.0/24) salen como private.
_INTERNAL_NETS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
)


def _public_ip(raw: str) -> str | None:
    try:
        addr = ipaddress.ip_address(raw.strip())
    except ValueError:
        return None
    if addr.is_loopback or addr.is_link_local or addr.is_multicast:
        return None
    if addr.is_unspecified:
        return None
    if any(addr in network for network in _INTERNAL_NETS):
        return None
    return str(addr)


def _walk(node: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, value
            yield from _walk(value, path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            path = f"{prefix}[{index}]"
            yield path, value
            yield from _walk(value, path)


def _finding_id(rule_id: str, source: str, extra: str) -> str:
    digest = hashlib.sha256(
        f"{rule_id}|{source}|{extra}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{rule_id}-{digest}"
