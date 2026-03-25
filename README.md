# Autonomy Stack Observatory

The shared measurement layer for the autonomy stack. Every vertical produces metrics and test results — the observatory collects them in one place, renders a dashboard, and generates daily reports.

This is the reference implementation for [Beoflow](https://beoflow.com). As patterns stabilize, generic tooling will be upstreamed to [autonomy-stack](https://github.com/ddfourtwo/autonomy-stack).

## How It Works

```
iOS repo ──── (playbook: E2E results + screenshots) ────┐
Web repo ──── (playbook: E2E results + screenshots) ─────┤
Backend repo ─ (playbook: unit/security/agent tests) ────┤
Sentry ─────── (cron: error stats) ──────────────────────┼──► observatory repo
PostHog ────── (cron: usage metrics) ────────────────────┤       │
Ad platforms ── (cron: marketing stats) ─────────────────┤       ▼
Website analytics (cron: traffic stats) ─────────────────┘   Svelte dashboard
                                                                  │
                                                         Agent reads recent commits
                                                                  │
                                                             Morning report
                                                            → Mattermost
```

Each repo has its own nightly playbooks (one per test type). Playbooks run tests, transform results to observatory JSON, and push to this repo. The dashboard builds at deploy time from the JSON data.

## Data Model

Every data file follows the same envelope:

```json
{
  "vertical": "product",
  "source": "unit-backend",
  "timestamp": "2026-03-25T09:00:00Z",
  "summary": { ... },
  "entries": [ ... ]
}
```

`summary` provides at-a-glance numbers. `entries` is source-specific detail. See `schemas/` for full definitions.

### Test Entry Standard Fields

All test entries (unit, E2E, agent) must include these fields for the dashboard to render properly:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Test method name (e.g. `test_rejects_expired_token`) |
| `module` | Yes | Module path for grouping by app (e.g. `ai_agent.tests.test_agent`) |
| `suite` | Recommended | Test class name (e.g. `WorkoutAgentInputValidationTest`). Groups tests within app sections. |
| `description` | Recommended | Human-readable docstring (e.g. "Expired JWT tokens should be rejected"). Shows in the dashboard Description column. |
| `status` | Yes | One of: `passed`, `failed`, `error`, `skipped`. `error` = infrastructure issue, `failed` = assertion failure. |
| `error` | When failed | Error message from traceback. Last line of the stack trace. |
| `duration_seconds` | Optional | Per-test timing. |
| `screenshot_url` | E2E only | `/media/` path to screenshot in R2. |
| `video_url` | E2E only | `/media/` path to video in R2. |

### Summary Standard Fields

| Field | Required | Description |
|-------|----------|-------------|
| `total` | Yes | Total test count |
| `passed` | Yes | Passed count |
| `failed` | Yes | Assertion failures |
| `errors` | Recommended | Infrastructure errors (import failures, timeouts) |
| `skipped` | Optional | Skipped tests |
| `duration_seconds` | Optional | Total run time |
| `coverage_percent` | Optional | Code coverage percentage |

## Dashboard Standards

The dashboard follows a Swagger-UI-inspired design (based on the Django security report at `/api/security-report/`). All detail pages must follow these patterns:

### Layout

1. **Dark topbar** with "Back to Observatory" link
2. **Title + metadata** (source name, date)
3. **Summary stat cards** — clickable to filter the table
4. **Stacked progress bar** (for pass/fail views)
5. **Filter indicator** when a filter is active
6. **Data table** with section grouping

### Test Detail Pages

- **Two-level grouping**: App section (e.g. "Ai Agent") → Test class (e.g. "WorkoutAgentInputValidationTest")
- **Collapsible sections**: Failing sections expanded and sorted to top; passing sections collapsed
- **Clickable stat cards**: Click Passed/Failed/Errors to filter the table to just that status
- **Columns**: Status icon | Test name + description (stacked) | Result badge
- **Test name**: Monospace font, method name
- **Description**: Grey, indented below test name (from test docstring)
- **Error messages**: Red left-border callout, monospace, inline below description
- **Result badges**: PASSED (green), FAILED (red), ERROR (orange), SKIPPED (grey)
- **Row highlighting**: Green tint for passed, red tint for failed/error

### Security Coverage Pages

- **Clickable stat cards**: Overall / Covered / Partial / Uncovered filter the endpoint matrix
- **Section grouping**: By API area (Ai, Dashboard, Workouts, etc.)
- **Columns**: Method badge (color-coded) | Endpoint path | Per-test-type ✓/✗/N/A | Total
- **Row highlighting**: Green for fully covered, amber for partial
- **N/A tooltips**: Hover shows reason why test type doesn't apply

### Home Page Cards

Each source gets a card showing:
- **Status indicator** (green/red/amber dot)
- **Key metric**: Pass count for tests, coverage % for security
- **Date** of last data
- Cards link to detail pages

## Playbook Architecture

Each test type in each repo gets its own playbook. Playbooks push to observatory.

| Repo | Playbook | Source | Deterministic? |
|------|----------|--------|---------------|
| `beoflow` | `backend-unit-tests` | `unit-backend` | 100% — always runs all |
| `beoflow` | `backend-security-tests` | `security-coverage` | 100% — always runs all |
| `beoflow` | `backend-agent-tests` | `agent-tests` | Gated — only if agent code changed |
| `beoflow-ios` | `ios-unit-tests` | `unit-ios` | 100% — always runs all |
| `beoflow-ios` | `ios-e2e-tests` | `e2e-ios` | Agent picks scope based on changes |
| `beoflow-webapp` | `web-unit-tests` | `unit-web` | 100% — always runs all |
| `beoflow-webapp` | `web-e2e-tests` | `e2e-web` | Agent picks scope based on changes |

### Playbook Standard Phases

Every test playbook follows this pattern:

1. **Run tests** (deterministic command)
2. **Transform results** (deterministic script → observatory JSON with all standard fields)
3. **Push to observatory** (`git add`, `commit`, `push`)

Agent-gated playbooks add a Phase 0: **Check for relevant changes** — skip if nothing changed.

### Transform Scripts

| Script | Input | Output |
|--------|-------|--------|
| `transform-django-tests.py` | Django `-v 2` stdout | `unit-test-results` envelope with docstrings, suite, errors |
| `transform-pytest.py` | pytest-json-report JSON | `unit-test-results` envelope |
| `transform-security-report.py` | Django security `report.json` | `security-coverage` envelope |

All transform scripts are deterministic — no LLM calls, no network, no judgment.

## Repo Structure

```
├── schemas/              JSON schemas for each data type
├── scripts/              Transform scripts and push helpers
├── collectors/           Cron-driven collectors for external APIs
├── report/               Morning report agent identity
├── dashboard/            Svelte static site (Cloudflare Pages)
└── data/                 The data itself (git-tracked JSON)
    ├── product/          Tests: unit, security, agent, E2E, Sentry
    ├── growth/           Facebook Ads, Google Ads
    ├── website/          Analytics
    ├── sales/            PostHog usage metrics
    ├── finance/          MRR, churn
    └── infrastructure/   Uptime, resource usage
```

## Media Storage

Screenshots and videos are stored in Cloudflare R2 (`observatory-media` bucket), not in git. Data files reference them by `/media/` paths. The dashboard proxies R2 through a Pages Function, gated by Cloudflare Access. No public URLs.

## Hosting

Deployed via Cloudflare Pages (auto-builds on push). Access restricted to `@beoflow.com` emails via Cloudflare Access.

## Adding a New Data Source

1. Create a schema in `schemas/` following the standard entry fields above
2. Create a transform script in `scripts/` that outputs the correct envelope with `suite`, `description`, `error`, and status categorization
3. Add data directory under `data/{vertical}/{source}/`
4. Create a playbook in the source repo following the standard phases
5. The dashboard auto-discovers new sources — no dashboard code changes needed

## Design Principles

- **Git as the database.** All data is committed JSON. History is free. Diffs are meaningful.
- **Push, don't pull.** Source repos push data in. The observatory never reaches into other systems at read time.
- **Schemas enforce consistency.** Every source conforms to the envelope format with standard fields.
- **Media lives in R2.** Binary assets in object storage, proxied through dashboard for access control.
- **Minimal code.** Static site, shell scripts, Python transform scripts. No frameworks, no backend.
- **Staff-only access.** Cloudflare Access gates the dashboard to `@beoflow.com` emails.
- **Swagger-style detail pages.** All test reports follow the same visual language: stat cards, section grouping, clickable filters, collapsible sections, inline error messages.
