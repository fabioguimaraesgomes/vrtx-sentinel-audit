import json
import sys
from pathlib import Path


def extract_severity_score(vuln: dict) -> float | None:
    severity = vuln.get("severity")
    if isinstance(severity, dict):
        score = severity.get("score")
        if isinstance(score, (int, float)):
            return float(score)
    score = vuln.get("cvss_score")
    if isinstance(score, (int, float)):
        return float(score)
    return None


def main(path_str: str) -> int:
    path = Path(path_str)
    data = json.loads(path.read_text(encoding="utf-8"))

    critical_hits = []
    for dep in data.get("dependencies", []):
        pkg = dep.get("name", "unknown")
        version = dep.get("version", "unknown")
        for vuln in dep.get("vulns", []):
            score = extract_severity_score(vuln)
            if score is not None and score >= 9.0:
                critical_hits.append(
                    {
                        "package": pkg,
                        "version": version,
                        "id": vuln.get("id", "unknown"),
                        "score": score,
                    }
                )

    if critical_hits:
        print("Critical vulnerabilities found (CVSS >= 9.0):")
        for hit in critical_hits:
            print(
                f"- {hit['package']}=={hit['version']} | {hit['id']} | score={hit['score']}"
            )
        return 1

    print("No critical vulnerabilities found by pip-audit metadata.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check_pip_audit_critical.py <pip-audit.json>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
