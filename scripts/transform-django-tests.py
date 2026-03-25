#!/usr/bin/env python3
"""Transform Django manage.py test output to observatory envelope format.

Parses the verbose (-v 2) output from Django's test runner.
Captures test names, docstrings, status, and error messages.

Usage: transform-django-tests.py <input.txt> <output.json> --source <source>

Deterministic — no LLM calls, no network, no judgment.
"""
import json
import re
import sys
from datetime import datetime, timezone


def parse_django_output(text: str) -> dict:
    """Parse Django test runner verbose output into structured results."""
    lines = text.split('\n')
    entries = []
    passed = 0
    failed = 0
    errored = 0
    skipped = 0

    # Django -v 2 output format (two lines per test):
    #
    #   test_name (module.Class.test_name)
    #   Docstring describing the test. ... ok
    #
    # With log noise between docstring and result:
    #   test_name (module.Class.test_name)
    #   Docstring. ... [log lines]
    #   [more log]
    #   ok

    name_pattern = re.compile(r'^(test\S+)\s+\(([^)]+)\)\s*$')
    # Result appears as "... ok" on the docstring line, or standalone "ok" after log noise
    result_pattern = re.compile(r'(?:^|\.\.\.\s*)(ok|FAIL|ERROR|skipped\b.*?)\s*$')
    # Docstring is the text before "..." on the line after the test name
    docstring_pattern = re.compile(r'^(.*?)\s*\.\.\.\s*')

    i = 0
    while i < len(lines):
        name_match = name_pattern.match(lines[i])
        if name_match:
            name = name_match.group(1)
            full_module = name_match.group(2)

            # Extract test class from module path
            # e.g. "ai_agent.tests.test_sanitize.SanitizeToolMarkersThinkTagTests.test_empty_think_block"
            # → class: "SanitizeToolMarkersThinkTagTests"
            # → module: "ai_agent.tests.test_sanitize"
            module_parts = full_module.split('.')
            test_class = None
            module = full_module
            for j, part in enumerate(module_parts):
                if part[0].isupper() and 'Test' in part:
                    test_class = part
                    module = '.'.join(module_parts[:j])
                    break

            # Capture docstring from the next line
            description = None
            if i + 1 < len(lines):
                doc_match = docstring_pattern.match(lines[i + 1])
                if doc_match:
                    desc = doc_match.group(1).strip()
                    # Don't use log lines as descriptions
                    if desc and not desc.startswith('[') and not desc.startswith('Traceback'):
                        description = desc

            # Scan forward for the result
            result = None
            for k in range(i + 1, len(lines)):
                # Stop if we hit the next test
                if name_pattern.match(lines[k]):
                    break
                result_match = result_pattern.search(lines[k])
                if result_match:
                    result = result_match.group(1).strip()
                    i = k
                    break

            if result == 'ok':
                status = 'passed'
                passed += 1
            elif result == 'FAIL':
                status = 'failed'
                failed += 1
            elif result == 'ERROR':
                status = 'error'
                errored += 1
            elif result and result.startswith('skipped'):
                status = 'skipped'
                skipped += 1
            else:
                status = 'unknown'

            if status != 'unknown':
                entries.append({
                    "name": name,
                    "module": module,
                    "suite": test_class,
                    "description": description,
                    "status": status,
                    "duration_seconds": None,
                    "error": None,
                })
        i += 1

    # Extract errors from FAIL/ERROR blocks at the bottom of the output
    # Format:
    #   ======================================================================
    #   FAIL: test_name (module.Class.test_name)
    #   Docstring.
    #   ----------------------------------------------------------------------
    #   Traceback (most recent call last):
    #     ...
    #   AssertionError: expected X got Y
    #
    #   ======================================================================
    error_block_pattern = re.compile(
        r'^(FAIL|ERROR): (test\S+)\s+\(([^)]+)\)',
        re.MULTILINE
    )

    # Split on separator lines to find error blocks
    separator = '=' * 70
    blocks = text.split(separator)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        header_match = error_block_pattern.match(block)
        if header_match:
            error_type = header_match.group(1)
            test_name = header_match.group(2)

            # Find the traceback after the dashed line
            dash_line = '-' * 70
            if dash_line in block:
                traceback_text = block.split(dash_line, 1)[1].strip()
                # Get the last line — the actual error message
                tb_lines = traceback_text.strip().split('\n')
                error_msg = tb_lines[-1].strip() if tb_lines else ''

                # Also grab a few lines of context for assertion errors
                if len(tb_lines) > 1 and ('assert' in error_msg.lower() or 'error' in error_msg.lower()):
                    # Keep it concise
                    if len(error_msg) > 500:
                        error_msg = error_msg[:500] + '...'

                # Match to the entry
                for entry in entries:
                    if entry["name"] == test_name and entry["error"] is None:
                        entry["error"] = error_msg
                        break

    # Parse total run time from "Ran X tests in Y.YYYs"
    time_match = re.search(r'Ran (\d+) tests? in (\d+\.\d+)s', text)
    duration = float(time_match.group(2)) if time_match else 0
    reported_total = int(time_match.group(1)) if time_match else 0

    total = passed + failed + errored + skipped

    # If we couldn't parse individual tests, use the summary line
    if total == 0 and reported_total > 0:
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
        "errors": errored,
        "skipped": skipped,
        "duration_seconds": round(duration, 1),
        "entries": entries,
    }


def transform(input_path: str, output_path: str, source: str):
    with open(input_path) as f:
        text = f.read()

    # Handle "skipping" placeholder
    if "Skipping" in text and len(text.strip().split('\n')) <= 2:
        result = {
            "vertical": "product",
            "source": source,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "total": 0, "passed": 0, "failed": 0, "errors": 0,
                "skipped": 0, "coverage_percent": None, "duration_seconds": 0,
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
    print(f"Transformed {s['total']} tests ({s['passed']} passed, {s['failed']} failed, {s['errors']} errors, {s['skipped']} skipped)")


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
