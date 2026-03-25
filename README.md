# Autonomy Stack Observatory

The shared measurement layer for the autonomy stack. Every vertical produces metrics and test results — the observatory collects them in one place, renders a dashboard, and generates daily reports.

This is the reference implementation for [Beoflow](https://beoflow.com). As patterns stabilize, generic tooling will be upstreamed to [autonomy-stack](https://github.com/ddfourtwo/autonomy-stack).

## How It Works

```
iOS repo ──── (CI: E2E results + screenshots) ─────┐
Web repo ──── (CI: E2E results + screenshots) ──────┤
Backend repo ─ (CI: unit test results) ─────────────┤
Sentry ─────── (cron: error stats) ─────────────────┼──► observatory repo
PostHog ────── (cron: usage metrics) ────────────────┤       │
Ad platforms ── (cron: marketing stats) ─────────────┤       ▼
Website analytics (cron: traffic stats) ────────────┘   Svelte dashboard
                                                             │
                                                    Agent reads recent commits
                                                             │
                                                        Morning report
                                                       → Mattermost
```

Each data source pushes a structured JSON file into this repo. Git history provides the changelog. A lightweight Svelte site renders the current state. A causeway agent diffs the last 24 hours and posts a morning report.

## Data Model

Every data file follows the same envelope:

```json
{
  "vertical": "product",
  "source": "e2e-ios",
  "timestamp": "2026-03-25T09:00:00Z",
  "summary": { ... },
  "entries": [ ... ]
}
```

`summary` provides at-a-glance numbers. `entries` is source-specific detail. See `schemas/` for full definitions.

## Repo Structure

```
├── schemas/              JSON schemas for each data type
├── scripts/              Push scripts (installed in source repos' CI)
├── collectors/           Cron-driven collectors for external APIs
├── report/               Morning report agent identity
├── dashboard/            Svelte static site
└── data/                 The data itself (git-tracked JSON)
    ├── product/          E2E tests, unit tests, Sentry
    ├── growth/           Facebook Ads, Google Ads
    ├── website/          Analytics
    ├── sales/            PostHog usage metrics
    ├── finance/          MRR, churn
    └── infrastructure/   Uptime, resource usage
```

## Vertical Mapping

| Vertical | Data Sources | Activate |
|----------|-------------|----------|
| **Product** | E2E tests (iOS, web), unit tests (backend), Sentry | Day 1 |
| **Sales** | PostHog usage metrics | Day 1 |
| **Infrastructure** | Uptime, resource usage | Day 1 |
| **Growth** | Facebook Ads, Google Ads | When campaigns active |
| **Website** | Umami / analytics | When marketing site exists |
| **Finance** | Stripe MRR, churn | When Stripe connected |
| **Support** | Ticket volume, resolution time | When support tooling exists |

## Media Storage

Screenshots and videos are stored in Cloudflare R2, not in git. Data files reference them by URL. Push scripts handle uploading media and embedding URLs.

## Morning Report

A causeway agent runs daily at 09:00. It reads `git log --since="24 hours ago"`, loads changed data files, compares with previous values, and posts a report highlighting:

- Tests that changed status (green/red transitions)
- New Sentry issues or trending errors
- Usage metrics with significant movement (>10%)
- Marketing performance anomalies

## Dashboard

Minimal Svelte static site. No backend. Reads JSON at build time. Shows health cards per vertical, test matrix with screenshots, trend sparklines, and a 24h diff view.

## Adding a New Data Source

1. Create a schema in `schemas/`
2. Create a collector in `collectors/` or push script in `scripts/`
3. Add data directory under `data/{vertical}/{source}/`
4. Add a card to the dashboard
5. Update the morning report prompt

## Design Principles

- **Git as the database.** All data is committed JSON. History is free. Diffs are meaningful.
- **Push, don't pull.** Source repos push data in. The observatory never reaches into other systems at read time.
- **Schemas enforce consistency.** Every source conforms to the envelope format.
- **Media lives in R2.** Binary assets in object storage. JSON references URLs.
- **Minimal code.** Static site, shell scripts, Python collectors. No frameworks, no backend, no auth.
