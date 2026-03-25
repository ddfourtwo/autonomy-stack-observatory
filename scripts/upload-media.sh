#!/usr/bin/env bash
# Upload media files (screenshots, videos) to R2 and output URLs.
#
# Usage: ./upload-media.sh <source> <file-or-directory>
# Example: ./upload-media.sh e2e-ios ./screenshots/
#
# Requires:
#   R2_BUCKET - R2 bucket name
#   R2_ENDPOINT - R2 endpoint URL
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY - R2 credentials (S3-compatible)
#   R2_PUBLIC_URL - Public URL prefix for the bucket
#
# Outputs one URL per line for each uploaded file.

set -euo pipefail

SOURCE="${1:?Usage: upload-media.sh <source> <file-or-directory>}"
INPUT="${2:?Usage: upload-media.sh <source> <file-or-directory>}"

DATE=$(date -u +%Y-%m-%d)
PREFIX="observatory/$SOURCE/$DATE"

upload_file() {
  local file="$1"
  local filename
  filename=$(basename "$file")
  local key="$PREFIX/$filename"

  aws s3 cp "$file" "s3://$R2_BUCKET/$key" \
    --endpoint-url "$R2_ENDPOINT" \
    --quiet

  echo "$R2_PUBLIC_URL/$key"
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
