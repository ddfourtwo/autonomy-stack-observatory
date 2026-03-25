#!/usr/bin/env bash
# Upload media files (screenshots, videos) to the private R2 bucket.
# Returns /media/ paths that resolve through the observatory dashboard proxy.
#
# Usage: ./upload-media.sh <source> <file-or-directory>
# Example: ./upload-media.sh e2e-ios ./screenshots/
#
# Requires:
#   R2_BUCKET - R2 bucket name (default: observatory-media)
#   R2_ENDPOINT - R2 endpoint URL (S3-compatible)
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY - R2 credentials
#
# Outputs one /media/ path per line for each uploaded file.
# These paths only work through the observatory site (behind Cloudflare Access).

set -euo pipefail

SOURCE="${1:?Usage: upload-media.sh <source> <file-or-directory>}"
INPUT="${2:?Usage: upload-media.sh <source> <file-or-directory>}"
R2_BUCKET="${R2_BUCKET:-observatory-media}"

DATE=$(date -u +%Y-%m-%d)
PREFIX="$SOURCE/$DATE"

upload_file() {
  local file="$1"
  local filename
  filename=$(basename "$file")
  local key="$PREFIX/$filename"

  aws s3 cp "$file" "s3://$R2_BUCKET/$key" \
    --endpoint-url "$R2_ENDPOINT" \
    --quiet

  echo "/media/$key"
}

if [ -d "$INPUT" ]; then
  for file in "$INPUT"/*; do
    [ -f "$file" ] && upload_file "$file"
  done
elif [ -f "$INPUT" ]; then
  upload_file "$INPUT"
else
  echo "Error: $INPUT is not a file or directory"
  exit 1
fi
