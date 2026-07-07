from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests


def _output_text(payload: dict) -> str:
    report = payload.get("report_draft") or {}
    return " | ".join(
        [
            str(payload.get("verdict", "")),
            str(payload.get("advisory", "")),
            json.dumps(report, sort_keys=True),
        ]
    ).lower()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "redteam" / "shield_cases.json").read_text(encoding="utf-8"))
    base_url = os.getenv("ECOTI_BASE_URL", "http://localhost:8001").rstrip("/")

    failures = []
    for case in cases:
        response = requests.post(
            f"{base_url}/api/shield/assess",
            json={
                "identifier": case["identifier"],
                "message": case["message"],
                "lang": case["lang"],
                "edge": True,
                "offline": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        text = _output_text(response.json())

        for needle in case.get("must_contain", []):
            if needle.lower() not in text:
                failures.append(f"{case['name']}: missing '{needle}'")

        any_values = [value.lower() for value in case.get("must_contain_any", [])]
        if any_values and not any(value in text for value in any_values):
            failures.append(f"{case['name']}: missing any of {any_values}")

        for needle in case.get("must_not_contain", []):
            if needle.lower() in text:
                failures.append(f"{case['name']}: found forbidden '{needle}'")

        print(f"{case['name']}: ok")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"\nAll {len(cases)} Shield red-team checks passed against {base_url}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
