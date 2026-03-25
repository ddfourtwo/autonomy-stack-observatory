#!/usr/bin/env python3
"""Transform pytest-json-report output to observatory envelope format.

Usage: transform-pytest.py <input.json> <output.json>

Deterministic — no LLM calls, no network, no judgment.
"""
import json
import sys
from datetime import datetime, timezone


def transform(input_path: str, output_path: str):
    with open(input_path) as f:
        report = json.load(f)

    tests = report.get("tests", [])

    entries = []
    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        outcome = test.get("outcome", "unknown")
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "skipped":
            skipped += 1

        # Extract module from nodeid: "tests/test_auth.py::TestAuth::test_login" → "tests.test_auth"
        nodeid = test.get("nodeid", "")
        parts = nodeid.split("::")
        module = parts[0].replace("/", ".").removesuffix(".py") if parts else ""
        name = parts[-1] if parts else nodeid

        error = None
        if outcome == "failed":
            call = test.get("call", {})
            crash = call.get("crash", {})
            error = crash.get("message", call.get("longrepr", ""))
            if isinstance(error, str) and len(error) > 500:
                error = error[:500] + "..."

        entries.append({
            "name": name,
            "module": module,
            "status": outcome,
            "duration_seconds": round(test.get("duration", 0), 3),
            "error": error,
        })

    # Coverage from pytest-cov (if present)
    coverage = None
    summary = report.get("summary", {})
    # pytest-json-report doesn't include coverage natively,
    # but if we add --cov --cov-report=json, we can merge it separately

    total = passed + failed + skipped
    duration = report.get("duration", 0)

    result = {
        "vertical": "product",
        "source": "unit-backend",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "coverage_percent": coverage,
            "duration_seconds": round(duration, 1),
        },
        "entries": entries,
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Transformed {total} tests ({passed} passed, {failed} failed, {skipped} skipped)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json>")
        sys.exit(1)
    transform(sys.argv[1], sys.argv[2])
