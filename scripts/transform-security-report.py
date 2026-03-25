#!/usr/bin/env python3
"""Transform Django security report.json to observatory format.

Usage: transform-security-report.py <report.json> <output.json>

Deterministic — no LLM calls, no network, no judgment.
"""
import json
import sys
from datetime import datetime, timezone


def transform(input_path: str, output_path: str):
    with open(input_path) as f:
        report = json.load(f)

    summary = report["summary"]
    test_types = list(summary["tests_by_type"].keys())

    # Group endpoints by section (first path segment after /api/v1/)
    sections = {}
    for ep in report["endpoints"]:
        path = ep["path"]
        # Extract section: /api/v1/ai/conversations/ → ai
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            section = parts[2].replace("-", " ").replace("_", " ").title()
        else:
            section = "Root"

        if section not in sections:
            sections[section] = []
        sections[section].append(ep)

    result = {
        "vertical": "product",
        "source": "security-coverage",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total_endpoints": summary["total_endpoints"],
            "overall_coverage": summary["overall_coverage"],
            "coverage": summary["coverage"],
            "tests_by_type": summary["tests_by_type"],
        },
        "test_types": test_types,
        "sections": {
            name: {
                "endpoints": endpoints,
                "stats": _section_stats(endpoints, test_types),
            }
            for name, endpoints in sorted(sections.items())
        },
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Transformed: {summary['total_endpoints']} endpoints, {summary['overall_coverage']}% overall coverage")


def _section_stats(endpoints, test_types):
    total = len(endpoints)
    fully_covered = 0
    for ep in endpoints:
        applicable = 0
        covered = 0
        for tt in test_types:
            if not ep.get(f"{tt}_na", False):
                applicable += 1
                if ep.get(f"{tt}_tested", False):
                    covered += 1
        if applicable > 0 and covered == applicable:
            fully_covered += 1
    pct = round((fully_covered / total) * 100) if total > 0 else 0
    return {"total": total, "fully_covered": fully_covered, "coverage_pct": pct}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <report.json> <output.json>")
        sys.exit(1)
    transform(sys.argv[1], sys.argv[2])
