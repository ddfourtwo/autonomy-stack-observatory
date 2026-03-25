#!/usr/bin/env bash
# Generic script to push a data file to the observatory repo.
# Called from CI pipelines or collector crons.
#
# Usage: ./push-data.sh <vertical> <source> <json-file>
# Example: ./push-data.sh product e2e-ios /tmp/e2e-results.json
#
# Requires: OBSERVATORY_REPO_PATH or OBSERVATORY_REPO_URL env var
# If OBSERVATORY_REPO_URL is set, clones a shallow copy, pushes, and cleans up.
# If OBSERVATORY_REPO_PATH is set, uses the local checkout.

set -euo pipefail

VERTICAL="${1:?Usage: push-data.sh <vertical> <source> <json-file>}"
SOURCE="${2:?Usage: push-data.sh <vertical> <source> <json-file>}"
JSON_FILE="${3:?Usage: push-data.sh <vertical> <source> <json-file>}"

DATE=$(date -u +%Y-%m-%d)
CLEANUP=""

if [ -n "${OBSERVATORY_REPO_PATH:-}" ]; then
  REPO="$OBSERVATORY_REPO_PATH"
elif [ -n "${OBSERVATORY_REPO_URL:-}" ]; then
  REPO=$(mktemp -d)
  git clone --depth 1 "$OBSERVATORY_REPO_URL" "$REPO"
  CLEANUP="$REPO"
else
  echo "Error: Set OBSERVATORY_REPO_PATH or OBSERVATORY_REPO_URL"
  exit 1
fi

TARGET_DIR="$REPO/data/$VERTICAL/$SOURCE"
mkdir -p "$TARGET_DIR"
cp "$JSON_FILE" "$TARGET_DIR/$DATE.json"

cd "$REPO"
git add "data/$VERTICAL/$SOURCE/$DATE.json"
git commit -m "data($VERTICAL/$SOURCE): $DATE"
git push origin main

if [ -n "$CLEANUP" ]; then
  rm -rf "$CLEANUP"
fi
