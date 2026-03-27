#!/usr/bin/env python3
"""Transform xcodebuild test output to observatory envelope format.

Parses console output from `xcodebuild test`.

Usage: transform-xctest.py <input.txt> <output.json> --source <source>

Deterministic — no LLM calls, no network, no judgment.
"""
import json
import re
import sys
from datetime import datetime, timezone


def parse_xcodebuild_output(text: str) -> dict:
    """Parse xcodebuild test console output.

    Modern format (Xcode 16+):
        Test case 'ClassName.testMethod()' passed on 'device' (N.NNN seconds)
        Test case 'ClassName.testMethod()' failed on 'device' (N.NNN seconds)

    Legacy ObjC format:
        Test Case '-[Module.ClassName testMethod]' passed (N.NNN seconds).

    Error lines:
        /path/file.swift:42: error: -[Module.Class testMethod] : XCTAssertEqual failed...
        /path/file.swift:42: error: ClassName.testMethod() : XCTAssertEqual failed...
    """
    entries = []
    passed = 0
    failed = 0
    skipped = 0

    # Modern format: Test case 'ClassName.testMethod()' passed on 'device' (N.NNN seconds)
    modern_pattern = re.compile(
        r"Test case '(\w+)\.(\w+)\(\)' (passed|failed) on '.*?' \((\d+\.\d+) seconds\)"
    )

    # Legacy format: Test Case '-[Module.ClassName testMethod]' passed (N.NNN seconds).
    legacy_pattern = re.compile(
        r"Test Case '-\[(\S+?)\.(\S+?)\s+(\S+?)\]' (passed|failed) \((\d+\.\d+) seconds\)\."
    )

    # Error lines — modern: ClassName.testMethod() : error message
    error_modern = re.compile(
        r":\d+: error: (\w+)\.(\w+)\(\) : (.+)"
    )
    # Error lines — legacy: -[Module.Class testMethod] : error message
    error_legacy = re.compile(
        r":\d+: error: -\[(\S+?)\.(\S+?)\s+(\S+?)\] : (.+)"
    )

    # Collect errors first
    errors = {}
    for match in error_modern.finditer(text):
        cls, method, msg = match.group(1), match.group(2), match.group(3).strip()
        key = (cls, method)
        if key not in errors:
            errors[key] = msg

    for match in error_legacy.finditer(text):
        cls, method, msg = match.group(2), match.group(3), match.group(4).strip()
        key = (cls, method)
        if key not in errors:
            errors[key] = msg

    # Parse modern format
    for match in modern_pattern.finditer(text):
        cls = match.group(1)
        method = match.group(2)
        result = match.group(3)
        duration = float(match.group(4))

        status = 'passed' if result == 'passed' else 'failed'
        if status == 'passed':
            passed += 1
        else:
            failed += 1

        entries.append({
            "name": method,
            "module": "BeoflowTests",
            "suite": cls,
            "description": None,
            "status": status,
            "duration_seconds": round(duration, 3),
            "error": errors.get((cls, method)),
        })

    # If no modern matches, try legacy format
    if not entries:
        for match in legacy_pattern.finditer(text):
            module = match.group(1)
            cls = match.group(2)
            method = match.group(3)
            result = match.group(4)
            duration = float(match.group(5))

            status = 'passed' if result == 'passed' else 'failed'
            if status == 'passed':
                passed += 1
            else:
                failed += 1

            entries.append({
                "name": method,
                "module": module,
                "suite": cls,
                "description": None,
                "status": status,
                "duration_seconds": round(duration, 3),
                "error": errors.get((cls, method)),
            })

    total = passed + failed + skipped

    # Parse total duration
    duration_match = re.search(r"Executed (\d+) tests?, with (\d+) failures?.*?in (\d+\.\d+)", text)
    total_duration = float(duration_match.group(3)) if duration_match else sum(e.get('duration_seconds') or 0 for e in entries)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": 0,
        "skipped": skipped,
        "duration_seconds": round(total_duration, 1),
        "entries": entries,
    }


def transform(input_path: str, output_path: str, source: str):
    with open(input_path) as f:
        text = f.read()

    parsed = parse_xcodebuild_output(text)

    result = {
        "vertical": "product",
        "source": source,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "total": parsed["total"],
            "passed": parsed["passed"],
            "failed": parsed["failed"],
            "errors": parsed["errors"],
            "skipped": parsed["skipped"],
            "coverage_percent": None,
            "duration_seconds": parsed["duration_seconds"],
        },
        "entries": parsed["entries"],
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    s = result["summary"]
    print(f"Transformed {s['total']} tests ({s['passed']} passed, {s['failed']} failed)")


if __name__ == "__main__":
    source = "unit-ios"
    args = sys.argv[1:]

    if "--source" in args:
        idx = args.index("--source")
        source = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <input.txt> <output.json> [--source <source>]")
        sys.exit(1)

    transform(args[0], args[1], source)
