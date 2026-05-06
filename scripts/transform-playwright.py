#!/usr/bin/env python3
"""Transform Playwright JSON reporter output to observatory e2e format.

Usage: transform-playwright.py <playwright.json> <output.json> [--source e2e-web]

Deterministic: no LLM calls, no network, no judgment.
"""
import json
import sys
from datetime import datetime, timezone


def iter_specs(suite):
    for spec in suite.get("specs", []):
        yield spec
    for child in suite.get("suites", []):
        yield from iter_specs(child)


def status_for(test):
    status = test.get("status")
    results = test.get("results") or []
    last = results[-1] if results else {}
    result_status = last.get("status")
    if status == "expected" or result_status == "passed":
        return "passed"
    if status == "skipped" or result_status == "skipped":
        return "skipped"
    if result_status in ("timedOut", "interrupted"):
        return "error"
    return "failed"


def error_for(test):
    results = test.get("results") or []
    for result in reversed(results):
        error = result.get("error") or {}
        message = error.get("message") or error.get("value")
        if message:
            return str(message).splitlines()[0][:500]
    return None


def artifacts_for(test):
    screenshot = None
    video = None
    for result in test.get("results") or []:
        for attachment in result.get("attachments") or []:
            name = attachment.get("name", "")
            content_type = attachment.get("contentType", "")
            path = attachment.get("path")
            if not path:
                continue
            if screenshot is None and ("screenshot" in name or content_type.startswith("image/")):
                screenshot = None
            if video is None and ("video" in name or content_type.startswith("video/")):
                video = None
    return screenshot, video


def transform(input_path, output_path, source):
    with open(input_path) as f:
        report = json.load(f)

    entries = []
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    duration_seconds = 0.0

    for suite in report.get("suites", []):
        for spec in iter_specs(suite):
            for test in spec.get("tests", []):
                status = status_for(test)
                counts[status] += 1
                duration_ms = sum((result.get("duration") or 0) for result in test.get("results") or [])
                duration_seconds += duration_ms / 1000
                screenshot, video = artifacts_for(test)
                suite_name = spec.get("file") or suite.get("title") or "e2e"
                entries.append({
                    "name": spec.get("title") or "unknown",
                    "suite": suite_name.replace(".spec.ts", "").replace(".spec.tsx", ""),
                    "description": spec.get("title") or None,
                    "status": status,
                    "duration_seconds": round(duration_ms / 1000, 3),
                    "screenshot_url": screenshot,
                    "video_url": video,
                    "error": error_for(test),
                })

    if not duration_seconds:
        duration_seconds = (report.get("stats", {}).get("duration") or 0) / 1000

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
    source = "e2e-web"
    args = sys.argv[1:]
    if "--source" in args:
        idx = args.index("--source")
        source = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <playwright.json> <output.json> [--source e2e-web]")
        sys.exit(1)
    transform(args[0], args[1], source)
