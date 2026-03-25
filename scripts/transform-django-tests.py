#!/usr/bin/env python3
"""Transform Django manage.py test output to observatory envelope format.

Parses the verbose (-v 2) output from Django's test runner.

Usage: transform-django-tests.py <input.txt> <output.json> --source <source>

Deterministic — no LLM calls, no network, no judgment.
"""
import json
import re
import sys
from datetime import datetime, timezone


def parse_django_output(text: str) -> dict:
    """Parse Django test runner verbose output into structured results."""
    entries = []
    passed = 0
    failed = 0
    errored = 0
    skipped = 0

    lines = text.split('\n')

    # Django -v 2 output format:
    #   test_name (module.Class.test_name)
    #   Docstring. ... ok          <-- may have log noise before "ok"
    #
    # Or with log noise:
    #   test_name (module.Class.test_name)
    #   Docstring. ... [log output]
    #   [more log output]
    #   ok
    #
    # Strategy: find test name lines, then scan forward for the result
    # (ok/FAIL/ERROR/skipped) which appears as a standalone word on a line.

    name_pattern = re.compile(r'^(test\S+)\s+\(([^)]+)\)\s*$')
    result_pattern = re.compile(r'(?:^|\.\.\.\s*)(ok|FAIL|ERROR|skipped\b.*?)\s*$')

    i = 0
    while i < len(lines):
        name_match = name_pattern.match(lines[i])
        if name_match:
            name = name_match.group(1)
            module = name_match.group(2)

            # Scan forward for the result — some tests produce thousands
            # of lines of log output between the name and ok/FAIL
            result = None
            for j in range(i + 1, len(lines)):
                # Check if we hit the next test (means we missed the result)
                if name_pattern.match(lines[j]):
                    break
                result_match = result_pattern.search(lines[j])
                if result_match:
                    result = result_match.group(1).strip()
                    i = j
                    break

            if result == 'ok':
                status = 'passed'
                passed += 1
            elif result == 'FAIL':
                status = 'failed'
                failed += 1
            elif result == 'ERROR':
                status = 'failed'
                errored += 1
            elif result and result.startswith('skipped'):
                status = 'skipped'
                skipped += 1
            else:
                # Couldn't find result — assume passed if overall OK
                status = 'unknown'

            if status != 'unknown':
                entries.append({
                    "name": name,
                    "module": module,
                    "status": status,
                    "duration_seconds": None,
                    "error": None,
                })
        i += 1

    # Try to extract errors from the FAIL/ERROR blocks
    # Format:
    #   ======================================================================
    #   FAIL: test_something (app.tests.TestClass)
    #   ----------------------------------------------------------------------
    #   Traceback (most recent call last):
    #     ...
    #   AssertionError: ...
    error_pattern = re.compile(
        r'^(?:FAIL|ERROR): (test\S+)\s+\(([^)]+)\)\s*\n'
        r'-+\n'
        r'(.*?)(?=\n={70}|\nRan \d|\Z)',
        re.MULTILINE | re.DOTALL
    )

    for match in error_pattern.finditer(text):
        name = match.group(1)
        module = match.group(2)
        traceback = match.group(3).strip()

        # Find the matching entry and add the error
        for entry in entries:
            if entry["name"] == name and entry["module"] == module and entry["error"] is None:
                # Take just the last line of the traceback (the actual error)
                lines = traceback.strip().split('\n')
                error_msg = lines[-1] if lines else traceback
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                entry["error"] = error_msg
                break

    # Parse total run time from "Ran X tests in Y.YYYs"
    time_match = re.search(r'Ran (\d+) tests? in (\d+\.\d+)s', text)
    duration = float(time_match.group(2)) if time_match else 0
    reported_total = int(time_match.group(1)) if time_match else 0

    total = passed + failed + errored + skipped

    # If we couldn't parse individual tests, use the summary line
    if total == 0 and reported_total > 0:
        # Check if the overall result was OK or FAILED
        if re.search(r'^OK', text, re.MULTILINE):
            passed = reported_total
            total = reported_total
        elif re.search(r'^FAILED', text, re.MULTILINE):
            fail_match = re.search(r'failures=(\d+)', text)
            err_match = re.search(r'errors=(\d+)', text)
            failed = int(fail_match.group(1)) if fail_match else 0
            errored = int(err_match.group(1)) if err_match else 0
            passed = reported_total - failed - errored
            total = reported_total

    return {
        "total": total,
        "passed": passed,
        "failed": failed + errored,
        "skipped": skipped,
        "duration_seconds": round(duration, 1),
        "entries": entries,
    }


def transform(input_path: str, output_path: str, source: str):
    with open(input_path) as f:
        text = f.read()

    # Handle "skipping security tests" placeholder
    if "Skipping" in text and len(text.strip().split('\n')) <= 2:
        result = {
            "vertical": "product",
            "source": source,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "coverage_percent": None,
                "duration_seconds": 0,
            },
            "entries": [],
        }
    else:
        parsed = parse_django_output(text)
        result = {
            "vertical": "product",
            "source": source,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "total": parsed["total"],
                "passed": parsed["passed"],
                "failed": parsed["failed"],
                "skipped": parsed["skipped"],
                "coverage_percent": None,
                "duration_seconds": parsed["duration_seconds"],
            },
            "entries": parsed["entries"],
        }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    s = result["summary"]
    print(f"Transformed {s['total']} tests ({s['passed']} passed, {s['failed']} failed, {s['skipped']} skipped)")


if __name__ == "__main__":
    source = "unit-backend"
    args = sys.argv[1:]

    if "--source" in args:
        idx = args.index("--source")
        source = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <input.txt> <output.json> [--source <source>]")
        sys.exit(1)

    transform(args[0], args[1], source)
