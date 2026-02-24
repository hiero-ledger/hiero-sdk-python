#!/usr/bin/env bash
set -euo pipefail

# Comment-based triage request script for PRs.
# Aligns with issue #1721: post a comment to request triage reviewers
# instead of assigning reviewers. Uses a triage list file or env var.
# Safety: defaults to dry-run mode unless DRY_RUN is explicitly set to 'false'.

if [ -z "${GITHUB_EVENT_PATH:-}" ] || [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "This script is intended to run inside GitHub Actions (needs GITHUB_EVENT_PATH and GITHUB_REPOSITORY)."
  exit 1
fi

PR_NUMBER=$(jq -r .pull_request.number < "$GITHUB_EVENT_PATH")
if [ "$PR_NUMBER" = "null" ] || [ -z "$PR_NUMBER" ]; then
  echo "No pull_request.number found in event payload"
  exit 0
fi

OWNER=${GITHUB_REPOSITORY%%/*}
REPO=${GITHUB_REPOSITORY##*/}
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "GITHUB_TOKEN not set"
  exit 1
fi

# Dry-run guard: default to true to avoid accidental state changes.
DRY_RUN=${DRY_RUN:-true}
DRY_RUN_LC=$(echo "$DRY_RUN" | tr '[:upper:]' '[:lower:]')
is_dry_run=true
if [ "$DRY_RUN_LC" = "false" ] || [ "$DRY_RUN_LC" = "0" ] || [ "$DRY_RUN_LC" = "no" ]; then
  is_dry_run=false
fi

# Determine triage reviewers: prefer file in repo, fallback to TRIAGE_REVIEWERS env var
TRIAGE_FILE=".github/triage-reviewers.txt"
if [ -f "$TRIAGE_FILE" ]; then
  TRIAGE_LIST=$(tr '\n' ' ' < "$TRIAGE_FILE" | xargs)
else
  TRIAGE_LIST="${TRIAGE_REVIEWERS:-}"
fi

if [ -z "$TRIAGE_LIST" ]; then
  echo "No triage reviewers configured. Provide .github/triage-reviewers.txt or TRIAGE_REVIEWERS env var."
  exit 1
fi

# Prepare mentions: accept comma or space separated values
mentions=$(echo "$TRIAGE_LIST" | sed -E 's/,/ /g')

MARKER='<!-- triage-request -->'
BODY_TEXT="${MARKER}\nRequesting triage review from: $mentions"

echo "PR #$PR_NUMBER in $OWNER/$REPO — triage mentions: $mentions"

# Idempotency: check existing comments for our marker
comments=$(curl -fS -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments")

if echo "$comments" | jq -r '.[].body' | grep -Fq "$MARKER"; then
  echo "Triage comment already present; skipping."
  exit 0
fi

if [ "$is_dry_run" = true ]; then
  echo "DRY RUN: would post comment to PR #$PR_NUMBER with body:" 
  echo "---"
  echo -e "$BODY_TEXT"
  echo "---"
  exit 0
fi

echo "Posting triage request comment to PR #$PR_NUMBER"
resp=$(curl -fS -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "User-Agent: hiero-sdk-bot" \
  -d "{\"body\": $(jq -n --arg b "$BODY_TEXT" '$b')}" \
  "https://api.github.com/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments")

# Use the response to avoid unused-variable warnings from static analyzers.
comment_id=$(echo "$resp" | jq -r '.id // empty')
if [ -n "$comment_id" ]; then
  echo "Comment posted successfully (id: $comment_id)"
else
  # If the response didn't include an id, show the raw response for debugging.
  echo "Comment posted; response: $resp"
fi
exit 0
