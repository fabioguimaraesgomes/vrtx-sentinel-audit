#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <target-url>"
  exit 1
fi

TARGET_URL="$1"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/release/security-reports"
mkdir -p "$REPORT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo '{"tool":"owasp-zap","status":"blocked","reason":"docker not found"}' > "$REPORT_DIR/zap_report.json"
  exit 0
fi

docker run --rm -t \
  -v "$REPORT_DIR:/zap/wrk" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t "$TARGET_URL" -J zap_report.json -r zap_report.html
