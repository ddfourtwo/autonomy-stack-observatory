#!/usr/bin/env python3
"""Transform Vitest JSON reporter output to observatory unit-test format.

Usage: transform-vitest.py <vitest.json> <output.json> [--source unit-web]

Deterministic: no LLM calls, no network, no judgment.
"""
import json
import os
import sys
from datetime import datetime, timezone


def status_for(assertion):
    status = assertion.get("status")
    if status == "passed":
        return "passed"
    if status == "failed":
        return "failed"
    if status in ("pending", "skipped", "todo"):
        return "skipped"
    return "error"


def module_for(path):
    path = path.replace("\\", "/")
    for marker in ("/src/", "/e2e/"):
        if marker in path:
            path = path.split(marker, 1)[1]
            break
    path = path.removesuffix(".test.tsx").removesuffix(".test.ts").removesuffix(".spec.tsx").removesuffix(".spec.ts")
    path = path.removesuffix(".tsx").removesuffix(".ts").removesuffix(".jsx").removesuffix(".js")
    return path.replace("/", ".")


def error_for(assertion):
    messages = assertion.get("failureMessages") or []
    if not messages:
        return None
    lines = [line.strip() for line in messages[0].splitlines() if line.strip()]
    if not lines:
        return None
    return lines[0][:500]


def transform(input_path, output_path, source):
    with open(input_path) as f:
        report = json.load(f)

    entries = []
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    duration_seconds = 0.0

    for result in report.get("testResults", []):
        module = module_for(result.get("name", "unknown"))
        for assertion in result.get("assertionResults", []):
            status = status_for(assertion)
            counts[status] += 1
            duration_ms = assertion.get("duration") or 0
            duration_seconds += duration_ms / 1000
            ancestors = assertion.get("ancestorTitles") or []
            entries.append({
                "name": assertion.get("title") or assertion.get("fullName") or "unknown",
                "module": module,
                "suite": " > ".join(ancestors) if ancestors else os.path.basename(module),
                "description": assertion.get("fullName") or None,
                "status": status,
                "duration_seconds": round(duration_ms / 1000, 3),
                "error": error_for(assertion),
            })

    result = {
        "vertical": "product",
        "source": source,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total": len(entries),
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["error"],
            "skipped": counts["skipped"],
            "coverage_percent": None,
            "duration_seconds": round(duration_seconds, 1),
        },
        "entries": entries,
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    s = result["summary"]
    print(f"Transformed {s['total']} tests ({s['passed']} passed, {s['failed']} failed, {s['errors']} errors, {s['skipped']} skipped)")


if __name__ == "__main__":
    source = "unit-web"
    args = sys.argv[1:]
    if "--source" in args:
        idx = args.index("--source")
        source = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <vitest.json> <output.json> [--source unit-web]")
        sys.exit(1)
    transform(args[0], args[1], source)
