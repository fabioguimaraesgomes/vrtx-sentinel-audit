#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/release/security-reports"
mkdir -p "$REPORT_DIR"

if [[ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]]; then
  PY="$ROOT_DIR/.venv/Scripts/python.exe"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PY="$ROOT_DIR/.venv/bin/python"
else
  PY="python"
fi

"$PY" -m pytest -q | tee "$REPORT_DIR/pytest.txt"
"$PY" -m bandit -r "$ROOT_DIR/src" -f json -o "$REPORT_DIR/bandit.json"
"$PY" -m pip_audit -r "$ROOT_DIR/requirements.txt" --format json --output "$REPORT_DIR/pip-audit.json"

if "$PY" -m semgrep --version >/dev/null 2>&1; then
  "$PY" -m semgrep --config=p/owasp "$ROOT_DIR/src" --json --output "$REPORT_DIR/semgrep.json" || true
else
  echo '{"tool":"semgrep","status":"blocked","reason":"semgrep not installed locally"}' > "$REPORT_DIR/semgrep.json"
fi
