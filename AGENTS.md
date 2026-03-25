# Agent Integration Guide

How to push test results, metrics, and media to the observatory from other repos.

## Overview

Your repo produces test results or metrics. A nightly playbook runs the tests, transforms results to observatory JSON, and pushes to this repo. The dashboard and morning report consume it.

## Data Entry Standards

Every test entry pushed to the observatory **must** include these fields for the dashboard to render correctly. Missing fields degrade the experience — descriptions show as blank, grouping falls flat, errors aren't visible.

### Required Fields

| Field | Type | Example | Why |
|-------|------|---------|-----|
| `name` | string | `test_rejects_expired_token` | Test method name — shown in monospace in the dashboard |
| `module` | string | `ai_agent.tests.test_agent` | Module path — used to group tests by app (first segment becomes the section header) |
| `status` | enum | `passed`, `failed`, `error`, `skipped` | `failed` = assertion failure, `error` = infrastructure issue. Dashboard uses different colors for each. |

### Strongly Recommended Fields

| Field | Type | Example | Why |
|-------|------|---------|-----|
| `suite` | string\|null | `WorkoutAgentInputValidationTest` | Test class name — creates sub-headers within app sections |
| `description` | string\|null | `"Expired JWT tokens should be rejected"` | Human-readable docstring — shows indented below test name. **This is what makes the report readable to non-developers.** |
| `error` | string\|null | `"AssertionError: expected 'active' but got 'expired'"` | Last line of traceback — shown in red callout for failed/error tests |

### Optional Fields

| Field | Type | When |
|-------|------|------|
| `duration_seconds` | number\|null | When per-test timing is available |
| `screenshot_url` | string\|null | E2E tests — `/media/` path to screenshot in R2 |
| `video_url` | string\|null | E2E tests — `/media/` path to video in R2 |

### Summary Fields

```json
{
  "total": 410,
  "passed": 271,
  "failed": 117,
  "errors": 22,
  "skipped": 0,
  "coverage_percent": null,
  "duration_seconds": 145.1
}
```

**Important:** Separate `failed` (assertion failures) from `errors` (infrastructure issues like import errors, timeouts, connection failures). The dashboard shows these as different colors (red vs orange) and they're independently filterable.

## Dashboard Behavior

Understanding how the dashboard renders your data helps you push better data.

### Home Page

Each source gets a card. Cards show pass/fail counts or coverage %. Green/red/amber indicator. Clickable → detail page.

### Detail Page — Test Results

The dashboard groups your entries into a **two-level hierarchy**:

1. **App section** — derived from `module` field (first segment: `ai_agent` → "Ai Agent")
2. **Test class** — from `suite` field (e.g. "WorkoutAgentInputValidationTest")

Within each class, tests are shown as rows with:
- Status icon (✓/✗)
- Test name (monospace) + description (grey, indented below)
- Error message (red callout with left border, if present)
- Result badge (PASSED/FAILED/ERROR)

**Collapsible sections**: Failing app sections auto-expand and sort to the top. Passing sections are collapsed by default.

**Clickable stat cards**: Clicking Passed/Failed/Errors filters the entire table to just that status. All sections auto-expand when filtering.

### Detail Page — Security Coverage

Endpoint × test type matrix (Auth, IDOR, Input, Rate, JWT, CORS, Sensitive). Clickable Covered/Partial/Uncovered filters.

## Transform Scripts

Use the provided scripts to convert test runner output to observatory format. They handle all the field extraction.

| Script | Input | Usage |
|--------|-------|-------|
| `transform-django-tests.py` | Django `manage.py test -v 2` stdout | `python3 scripts/transform-django-tests.py output.txt result.json --source unit-backend` |
| `transform-pytest.py` | pytest-json-report JSON | `python3 scripts/transform-pytest.py output.json result.json` |
| `transform-security-report.py` | Django security `report.json` | `python3 scripts/transform-security-report.py report.json result.json` |

The Django transformer automatically extracts:
- Test docstrings → `description`
- Test class names → `suite`
- Error messages from FAIL/ERROR traceback blocks → `error`
- `failed` vs `error` status distinction

### Writing a New Transform Script

When adding a new test framework, your transform script must:
1. Output the standard envelope format
2. Populate `suite` and `description` — don't leave them null if the data is available
3. Distinguish `failed` (assertion) from `error` (infrastructure) in both entries and summary
4. Extract error messages — at minimum the last line of the traceback
5. Be fully deterministic — no LLM calls, no network, no judgment

## Playbook Structure

Every test playbook follows these standard phases:

```
Phase 1 (optional): Check for relevant changes — skip if nothing changed
Phase 2: Run tests (deterministic command)
Phase 3: Transform results (deterministic script)
Phase 4: Push to observatory (git add, commit, push)
```

See the `beoflow/.playbooks/` directory for examples:
- `backend-unit-tests/` — fully deterministic, 3 phases
- `backend-security-tests/` — fully deterministic, 4 phases
- `backend-agent-tests/` — gated on code changes, 5 phases

## Pushing Data

```bash
# From the playbook's final phase:
cd /path/to/autonomy-stack-observatory
DATE=$(date -u +%Y-%m-%d)
git pull origin main --ff-only
cp /tmp/results.json data/<vertical>/<source>/$DATE.json
git add data/<vertical>/<source>/$DATE.json
git commit -m "data(<source>): $DATE"
git push origin main
```

## Uploading Media (Screenshots, Videos)

Media goes to the private R2 bucket (`observatory-media`). The dashboard serves it through `/media/*`, gated by Cloudflare Access.

```bash
./scripts/upload-media.sh <source> /path/to/file-or-directory
# Output: /media/<source>/2026-03-25/filename.png
```

Reference `/media/` paths in your JSON entries — never direct R2 URLs.

## Available Sources

| Vertical | Source | Schema | Playbook |
|----------|--------|--------|----------|
| `product` | `unit-backend` | `unit-test-results.schema.json` | `backend-unit-tests` |
| `product` | `security-coverage` | `security-coverage.schema.json` | `backend-security-tests` |
| `product` | `agent-tests` | `unit-test-results.schema.json` | `backend-agent-tests` |
| `product` | `unit-ios` | `unit-test-results.schema.json` | `ios-unit-tests` |
| `product` | `e2e-ios` | `e2e-results.schema.json` | `ios-e2e-tests` |
| `product` | `unit-web` | `unit-test-results.schema.json` | `web-unit-tests` |
| `product` | `e2e-web` | `e2e-results.schema.json` | `web-e2e-tests` |
| `product` | `sentry` | `sentry-stats.schema.json` | collector cron |
| `sales` | `usage` | `usage-metrics.schema.json` | collector cron |
| `growth` | `facebook-ads` | `marketing-stats.schema.json` | collector cron |
| `growth` | `google-ads` | `marketing-stats.schema.json` | collector cron |
| `website` | `analytics` | `website-stats.schema.json` | collector cron |

## Credential Access

Agents running in causeway sessions should access R2 and GitHub credentials via the credential proxy — never hardcode or read secrets directly.
