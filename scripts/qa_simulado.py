"""QA simulado end-to-end del MVP file-first (ingest/checks/score/report).

Uso (desde la raiz del Simulador, LLM_PROVIDER=off):
  python scripts/qa_simulado.py

No habilita llamadas xAI. Sale 0 si todo verde.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Determinista: nunca LLM en este QA.
os.environ["LLM_PROVIDER"] = "off"
os.environ.pop("XAI_API_KEY", None)

from services.checks_basic import run_checks  # noqa: E402
from services.ingest import ingest_file  # noqa: E402
from services.models import Evidence, to_dict, to_json  # noqa: E402
from services.report import draft_report  # noqa: E402
from services.score import score_findings  # noqa: E402

FIXTURES = ROOT / "mocks" / "fixtures"
PASS = 0
FAIL = 0
RESULTS: list[dict] = []


def _record(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


def _pipeline(path: Path):
    evidences = ingest_file(path)
    findings = run_checks(evidences)
    score = score_findings(findings)
    report = draft_report(findings, score, lang="es", client_id="qa-simulado")
    return evidences, findings, score, report


def test_happy_sample_iam() -> None:
    path = FIXTURES / "sample_iam.json"
    evidences, findings, score, report = _pipeline(path)
    codes = {f.rule_id for f in findings}
    ok = (
        len(evidences) == 3
        and score.total == 27.0
        and score.grade == "F"
        and "VRTX-IAM-OWNER" in codes
        and "VRTX-IAM-PRIMITIVE" in codes
        and "VRTX-STORAGE-PUBLIC" in codes
        and "VRTX-NET-EXTERNAL-IP" in codes
        and bool(report.title)
        and len(report.remediations) >= 4
    )
    _record(
        "happy_path_sample_iam",
        ok,
        f"score={score.total} findings={len(findings)} title={bool(report.title)}",
    )


def test_empty_json_list() -> None:
    path = FIXTURES / "empty_list.json"
    evidences, findings, score, report = _pipeline(path)
    codes = [f.rule_id for f in findings]
    ok = (
        evidences == []
        and codes == ["VRTX-INGEST-OK"]
        and score.total == 0.0
        and score.grade == "A"
        and bool(report.title)
    )
    _record("empty_json_list", ok, f"ev={len(evidences)} codes={codes}")


def test_empty_csv() -> None:
    path = FIXTURES / "empty.csv"
    evidences, findings, score, _report = _pipeline(path)
    ok = evidences == [] and score.total == 0.0
    _record("empty_csv", ok, f"ev={len(evidences)} score={score.total}")


def test_malformed_json_clean_error() -> None:
    path = FIXTURES / "malformed.json"
    try:
        ingest_file(path)
        _record("malformed_json", False, "no lanzo error")
    except ValueError as exc:
        msg = str(exc)
        ok = "JSON malformado" in msg and "Traceback" not in msg
        _record("malformed_json", ok, msg)
    except Exception as exc:  # noqa: BLE001
        _record(
            "malformed_json",
            False,
            f"tipo inesperado {type(exc).__name__}: {exc}",
        )


def test_missing_file() -> None:
    path = FIXTURES / "no_such_file_xyz.json"
    try:
        ingest_file(path)
        _record("missing_file", False, "no lanzo FileNotFoundError")
    except FileNotFoundError as exc:
        _record("missing_file", "No existe" in str(exc), str(exc))
    except Exception as exc:  # noqa: BLE001
        _record("missing_file", False, f"{type(exc).__name__}: {exc}")


def test_csv_iam_like() -> None:
    path = FIXTURES / "sample_iam_rows.csv"
    evidences, findings, score, report = _pipeline(path)
    codes = {f.rule_id for f in findings}
    ok = (
        len(evidences) == 3
        and "VRTX-IAM-OWNER" in codes
        and "VRTX-STORAGE-PUBLIC" in codes
        and "VRTX-NET-EXTERNAL-IP" in codes
        and score.total == 22.0
        and bool(report.title)
    )
    _record("csv_iam_like", ok, f"score={score.total} codes={sorted(codes)}")


def test_auth_burst() -> None:
    path = FIXTURES / "auth_burst.json"
    _evidences, findings, score, report = _pipeline(path)
    codes = {f.rule_id for f in findings}
    burst = [f for f in findings if f.rule_id == "VRTX-AUTH-FAILED-BURST"]
    ok = (
        "VRTX-AUTH-FAILED-BURST" in codes
        and len(burst) == 1
        and burst[0].severity in {"medium", "high"}
        and score.total >= 5.0
        and any(r.get("code") == "VRTX-AUTH-FAILED-BURST" for r in report.remediations)
    )
    _record(
        "auth_burst_ge3",
        ok,
        f"codes={sorted(codes)} sev={burst[0].severity if burst else None}",
    )


def test_auth_low() -> None:
    path = FIXTURES / "auth_low.json"
    _evidences, findings, score, _report = _pipeline(path)
    codes = {f.rule_id for f in findings}
    ok = "VRTX-AUTH-FAILED-BURST" not in codes and "VRTX-INGEST-OK" in codes
    _record("auth_low_lt3", ok, f"codes={sorted(codes)} score={score.total}")


def test_draft_report_contract() -> None:
    path = FIXTURES / "sample_iam.json"
    _e, findings, score, report = _pipeline(path)
    serialized = to_json(report)
    parsed = json.loads(serialized)
    known = {
        "VRTX-STORAGE-PUBLIC",
        "VRTX-IAM-OWNER",
        "VRTX-IAM-PRIMITIVE",
        "VRTX-NET-EXTERNAL-IP",
    }
    rem_codes = {r.get("code") for r in report.remediations}
    ok = (
        isinstance(report.title, str)
        and len(report.title.strip()) > 0
        and known.issubset(rem_codes)
        and all(r.get("suggestion") for r in report.remediations)
        and isinstance(parsed, dict)
        and "findings" in parsed
        and "score" in parsed
    )
    _record(
        "draft_report_contract",
        ok,
        f"title_len={len(report.title)} rems={len(report.remediations)}",
    )


def test_llm_off_no_network() -> None:
    calls: list[object] = []
    orig = urllib.request.urlopen

    def _boom(*args, **kwargs):  # noqa: ANN001
        calls.append({"args": args, "kwargs": kwargs})
        raise AssertionError("NETWORK CALLED under LLM_PROVIDER=off")

    urllib.request.urlopen = _boom  # type: ignore[assignment]
    try:
        os.environ["LLM_PROVIDER"] = "off"
        os.environ["XAI_API_KEY"] = "should-not-be-used"
        path = FIXTURES / "sample_iam.json"
        _pipeline(path)
        # Tambien via adaptador directo
        from services.xai_adapter import maybe_rewrite_summary

        _e, findings, score, report = _pipeline(path)
        maybe_rewrite_summary(report)
        ok = calls == []
        _record("llm_provider_off_no_network", ok, f"calls={len(calls)}")
    finally:
        urllib.request.urlopen = orig
        os.environ["LLM_PROVIDER"] = "off"
        os.environ.pop("XAI_API_KEY", None)


def test_path_with_spaces() -> None:
    path = FIXTURES / "path with spaces" / "auth low.json"
    evidences, findings, score, report = _pipeline(path)
    ok = len(evidences) == 1 and score.total == 0.0 and bool(report.title)
    _record("path_with_spaces", ok, f"ev={len(evidences)} score={score.total}")


def test_none_payload_safety() -> None:
    ev = Evidence(kind="auth", source="qa", payload=None, ingested_at="t")  # type: ignore[arg-type]
    try:
        findings = run_checks([ev])
        score = score_findings(findings)
        report = draft_report(findings, score)
        ok = bool(report.title) and score.total == 0.0
        _record("none_payload_safety", ok, f"findings={[f.rule_id for f in findings]}")
    except Exception as exc:  # noqa: BLE001
        _record("none_payload_safety", False, f"{type(exc).__name__}: {exc}")


def test_bad_encoding_clean_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "latin1.json"
        path.write_bytes(b'[{"kind":"auth","note":"\xe9"}]')
        try:
            ingest_file(path)
            _record("bad_encoding", False, "no lanzo error")
        except ValueError as exc:
            _record("bad_encoding", "Encoding no valido" in str(exc), str(exc))
        except Exception as exc:  # noqa: BLE001
            _record("bad_encoding", False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    print(f"QA simulado VRTX Sentinel — root={ROOT}")
    print(f"LLM_PROVIDER={os.environ.get('LLM_PROVIDER')}")
    tests = [
        test_happy_sample_iam,
        test_empty_json_list,
        test_empty_csv,
        test_malformed_json_clean_error,
        test_missing_file,
        test_csv_iam_like,
        test_auth_burst,
        test_auth_low,
        test_draft_report_contract,
        test_llm_off_no_network,
        test_path_with_spaces,
        test_none_payload_safety,
        test_bad_encoding_clean_error,
    ]
    for fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _record(fn.__name__, False, f"CRASH {type(exc).__name__}: {exc}")
            traceback.print_exc()

    summary = {
        "ok": FAIL == 0,
        "passed": PASS,
        "failed": FAIL,
        "total": PASS + FAIL,
        "results": RESULTS,
        "smoke_score_expected": 27.0,
    }
    # Re-assert smoke contract
    _e, _f, smoke_score, smoke_report = _pipeline(FIXTURES / "sample_iam.json")
    summary["smoke_score"] = smoke_score.total
    summary["smoke_findings"] = len(_f)
    summary["smoke_title"] = smoke_report.title
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if smoke_score.total != 27.0:
        print("ASSERT FAIL: smoke score != 27")
        return 1
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
