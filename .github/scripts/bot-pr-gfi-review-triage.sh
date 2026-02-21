#!/usr/bin/env bash
set -euo pipefail

# Simple script to request a reviewer for a PR when invoked from GitHub Actions.
# Expects: GITHUB_EVENT_PATH and GITHUB_REPOSITORY to be set by Actions and
# a valid GITHUB_TOKEN in the environment.

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
REVIEWER="coderabbit"
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "GITHUB_TOKEN not set"
  exit 1
fi

echo "Checking existing requested reviewers for PR #$PR_NUMBER in $OWNER/$REPO"
existing=$(curl -sS -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/requested_reviewers")

if echo "$existing" | jq -e --arg r "$REVIEWER" '.users[]?.login == $r' >/dev/null 2>&1; then
  echo "User $REVIEWER already requested for PR #$PR_NUMBER"
  exit 0
fi

echo "Requesting reviewer $REVIEWER for PR #$PR_NUMBER"
resp=$(curl -sS -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  -d "{\"reviewers\":[\"$REVIEWER\"]}" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/requested_reviewers")

if echo "$resp" | jq -e '.errors? // empty' >/dev/null 2>&1; then
  echo "Request API returned an error: $resp"
  exit 1
fi

echo "Requested $REVIEWER for PR #$PR_NUMBER successfully"
exit 0
