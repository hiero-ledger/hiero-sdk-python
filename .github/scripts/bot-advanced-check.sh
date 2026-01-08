#!/bin/bash
set -euo pipefail

log() {
  echo "[advanced-check] $1"
}

# Required env vars
if [[ -z "${REPO:-}" ]] || [[ -z "${ISSUE_NUMBER:-}" ]] || [[ -z "${GH_TOKEN:-}" ]]; then
  log "ERROR: Missing required environment variables"
  exit 1
fi

# IMPORTANT SAFETY:
# If no trigger assignee exists (i.e. label event), do nothing
if [[ -z "${TRIGGER_ASSIGNEE:-}" ]]; then
  log "No trigger assignee detected (label-only event). Skipping enforcement."
  exit 0
fi

check_user() {
  local user=$1
  log "Checking @$user..."

  # Skip core contributors
  PERMISSION=$(gh api "repos/$REPO/collaborators/$user/permission" \
    --jq '.permission' 2>/dev/null || echo "none")

  if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
    log "@$user is core ($PERMISSION). Skipping."
    return 0
  fi

  # Count completed intermediate ISSUES or PRs
  INT_QUERY="repo:$REPO is:closed (is:issue OR is:pr) label:intermediate -reason:\"not planned\" (author:$user OR assignee:$user)"
  INT_COUNT=$(gh api search/issues -f q="$INT_QUERY" --jq '.total_count' || echo "0")

  [[ "$INT_COUNT" =~ ^[0-9]+$ ]] || INT_COUNT=0

  if (( INT_COUNT >= 1 )); then
    log "@$user qualified."
    return 0
  fi

  log "@$user not qualified. Unassigning."

  MSG="Hi @$user, I can’t assign you to this issue yet.

**Why?**  
Advanced issues involve high-risk changes to core systems and require prior experience.

**Requirement:**  
- Complete at least **1 intermediate issue** (You have: **$INT_COUNT**)

Please check out available [intermediate issues](https://github.com/$REPO/labels/intermediate) to build your experience first."

  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
  gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$user"
}

check_user "$TRIGGER_ASSIGNEE"
