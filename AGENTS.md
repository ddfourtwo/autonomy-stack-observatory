# Agent Integration Guide

How to push data and media to the observatory from other repos.

## Overview

Your repo produces test results, metrics, or other data. You push structured JSON to this observatory repo, and optionally upload screenshots/videos to R2. The observatory dashboard and morning report consume it.

## Pushing Data

Use the `push-data.sh` script or replicate its logic:

```bash
# From your CI or cron job:
./scripts/push-data.sh <vertical> <source> /path/to/results.json

# Example: push iOS E2E results
./scripts/push-data.sh product e2e-ios /tmp/e2e-results.json
```

This clones the observatory repo (shallow), copies your JSON into `data/<vertical>/<source>/<date>.json`, commits, and pushes.

**Environment variables:**
- `OBSERVATORY_REPO_URL` — the repo URL (for shallow clone + push)
- OR `OBSERVATORY_REPO_PATH` — path to a local checkout

### Data Format

Every file must follow the envelope format:

```json
{
  "vertical": "product",
  "source": "e2e-ios",
  "timestamp": "2026-03-25T09:00:00Z",
  "summary": { ... },
  "entries": [ ... ]
}
```

See `schemas/` for the full schema for each data type. Your `vertical` and `source` must match the directory you're pushing to.

### Doing It Without the Script

If you can't run the shell script (e.g. from a Swift/Python context), the logic is:

1. Clone: `git clone --depth 1 <observatory-repo-url> /tmp/observatory`
2. Write your JSON to `data/<vertical>/<source>/<YYYY-MM-DD>.json`
3. Commit: `git add data/ && git commit -m "data(<vertical>/<source>): <date>"`
4. Push: `git push origin main`

## Uploading Media (Screenshots, Videos)

Media goes to the private R2 bucket. The dashboard serves it through `/media/*`, gated by Cloudflare Access. No public URLs.

```bash
# Upload a single file
./scripts/upload-media.sh e2e-ios /path/to/screenshot.png
# Output: /media/e2e-ios/2026-03-25/screenshot.png

# Upload a directory of files
./scripts/upload-media.sh e2e-ios ./screenshots/
# Output: one /media/ path per line
```

**Environment variables:**
- `R2_ENDPOINT` — your Cloudflare R2 S3-compatible endpoint
- `AWS_ACCESS_KEY_ID` — R2 API token access key
- `AWS_SECRET_ACCESS_KEY` — R2 API token secret key
- `R2_BUCKET` — bucket name (default: `observatory-media`)

### R2 Key Convention

Files are stored as `<source>/<date>/<filename>`:
```
e2e-ios/2026-03-25/login-screen.png
e2e-web/2026-03-25/dashboard.png
```

The returned `/media/` paths map directly to these keys.

### Using Media URLs in Data

Reference the `/media/` paths in your JSON entries:

```json
{
  "name": "Login - Email and Password",
  "suite": "Authentication",
  "status": "passed",
  "screenshot_url": "/media/e2e-ios/2026-03-25/login-email.png",
  "video_url": null
}
```

### Uploading Without the Script

Use any S3-compatible client. The key format is `<source>/<date>/<filename>`:

```python
import boto3

s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

key = f"e2e-ios/2026-03-25/screenshot.png"
s3.upload_file('/tmp/screenshot.png', 'observatory-media', key)
media_path = f"/media/{key}"
```

```swift
// Use AWS SDK for Swift or a simple S3 PUT request
let key = "e2e-ios/\(dateString)/\(filename)"
// Upload to observatory-media bucket
let mediaPath = "/media/\(key)"
```

## Credential Access

Agents running in causeway sessions should access R2 credentials via the credential proxy — never hardcode or read secrets directly.

Observatory repo access (for git push) requires a GitHub token with write access to `ddfourtwo/autonomy-stack-observatory`.

## Available Verticals and Sources

| Vertical | Source | Schema |
|----------|--------|--------|
| `product` | `e2e-ios` | `schemas/e2e-results.schema.json` |
| `product` | `e2e-web` | `schemas/e2e-results.schema.json` |
| `product` | `unit-backend` | `schemas/unit-test-results.schema.json` |
| `product` | `sentry` | `schemas/sentry-stats.schema.json` |
| `sales` | `usage` | `schemas/usage-metrics.schema.json` |
| `growth` | `facebook-ads` | `schemas/marketing-stats.schema.json` |
| `growth` | `google-ads` | `schemas/marketing-stats.schema.json` |
| `website` | `analytics` | `schemas/website-stats.schema.json` |

To add a new source, create the schema and data directory first. See `README.md` for the procedure.
