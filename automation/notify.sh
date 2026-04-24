#!/bin/bash

# Send Telegram notification for CI/CD pipeline failures
# Usage: notify.sh <workflow_name> <status> <details>

TELEGRAM_TOKEN="${TELEGRAM_TOKEN}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID}"
WORKFLOW_NAME="${1:-CI/CD Pipeline}"
STATUS="${2:-failed}"
DETAILS="${3:-Unknown error}"
GITHUB_REPO="${GITHUB_REPOSITORY:-aws-hybrid}"
GITHUB_SHA="${GITHUB_SHA:-unknown}"
GITHUB_REF="${GITHUB_REF:-unknown}"
GITHUB_ACTOR="${GITHUB_ACTOR:-unknown}"
RUN_ID="${GITHUB_RUN_ID:-unknown}"

if [[ -z "$TELEGRAM_TOKEN" || -z "$TELEGRAM_CHAT_ID" ]]; then
  echo "❌ Telegram credentials not configured. Skipping notification."
  exit 0
fi

# Format message with context (using HTML format instead of Markdown to avoid parsing issues)
MESSAGE="🚨 <b>CI/CD Pipeline Failure</b>

<b>Workflow:</b> $WORKFLOW_NAME
<b>Repository:</b> $GITHUB_REPO
<b>Branch:</b> $GITHUB_REF
<b>Commit:</b> ${GITHUB_SHA:0:7}
<b>Triggered by:</b> $GITHUB_ACTOR

<b>Error:</b> $DETAILS

<b>Action:</b> Check logs at GitHub Actions Run #$RUN_ID"

# Send notification
TELEGRAM_API="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"

response=$(curl -s -X POST "$TELEGRAM_API" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=${MESSAGE}" \
  -d "parse_mode=HTML")

# Check response
if echo "$response" | grep -q '"ok":true'; then
  echo "✅ Notification sent successfully"
  exit 0
else
  echo "⚠️  Failed to send Telegram notification"
  echo "Response: $response"
  exit 1
fi
