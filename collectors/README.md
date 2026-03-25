# Collectors

Cron-driven scripts that fetch metrics from external APIs and push them to the observatory.

Each collector:
1. Calls an external API (Sentry, PostHog, Facebook Ads, etc.)
2. Transforms the response into the observatory envelope format
3. Writes a JSON file to `data/{vertical}/{source}/{date}.json`
4. Commits and pushes

## Setup

```bash
pip install -r requirements.txt
```

## Configuration

Each collector reads credentials from environment variables. Never hardcode API keys.

| Collector | Required env vars |
|-----------|------------------|
| `sentry.py` | `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` |
| `posthog.py` | `POSTHOG_API_KEY`, `POSTHOG_PROJECT_ID` |
| `facebook_ads.py` | `FB_ACCESS_TOKEN`, `FB_AD_ACCOUNT_ID` |
| `google_ads.py` | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID` |
| `website_analytics.py` | `UMAMI_API_URL`, `UMAMI_TOKEN`, `UMAMI_WEBSITE_ID` |

All collectors also need `OBSERVATORY_REPO_PATH` pointing to the local checkout.
