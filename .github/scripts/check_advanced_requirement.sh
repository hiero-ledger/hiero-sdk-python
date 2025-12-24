#!/bin/bash
set -euo pipefail

# 1. Validate required environment variables
if [[ -z "${REPO:-}" ]] || [[ -z "${ISSUE_NUMBER:-}" ]]; then
  echo "ERROR: Required environment variables REPO and ISSUE_NUMBER must be set"
  exit 1
fi

# Function to check a single user
check_user() {
  local user=$1
  echo "[advanced-check] Checking qualification for @$user..."

  # Permission exemption
  PERM_JSON=$(gh api "repos/$REPO/collaborators/$user/permission" 2>/dev/null || echo '{"permission":"none"}')
  PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission // "none"')

  if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
    echo "[advanced-check] User @$user is core member ($PERMISSION). Skipping."
    return 0
  fi

  # Get counts
  GFI_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"good first issue\""
  INT_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"intermediate\""

  GFI_COUNT=$(gh api "search/issues" -f q="$GFI_QUERY" --jq '.total_count' || echo "0")
  INT_COUNT=$(gh api "search/issues" -f q="$INT_QUERY" --jq '.total_count' || echo "0")

  # Numeric validation
  if ! [[ "$GFI_COUNT" =~ ^[0-9]+$ ]]; then GFI_COUNT=0; fi
  if ! [[ "$INT_COUNT" =~ ^[0-9]+$ ]]; then INT_COUNT=0; fi

  # Validation Logic
  if (( GFI_COUNT >= 1 )) && (( INT_COUNT >= 1 )); then
    echo "[advanced-check] User @$user qualified."
    return 0
  else
    echo "[advanced-check] User @$user failed. Unassigning..."

    # Tailor the suggestion
    if (( GFI_COUNT == 0 )); then
      SUGGESTION="[good first issue](https://github.com/$REPO/labels/good%20first%20issue)"
    else
      SUGGESTION="[intermediate issue](https://github.com/$REPO/labels/intermediate)"
    fi

    # Post the message FIRST, then unassign.
    # This ensures the user sees the explanation even if the unassign call has issues.
    MSG="Hi @$user, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase. They require significant testing and can impact automation and CI behavior.

**Requirement:**
- Complete at least **1** 'good first issue' (You have: **$GFI_COUNT**)
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please check out our **$SUGGESTION** tasks to build your experience first!"

    gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$user"
  fi
}

# --- Main Logic ---

log() { echo "[advanced-check] $1"; }

if [[ -n "${TRIGGER_ASSIGNEE:-}" ]]; then
  check_user "$TRIGGER_ASSIGNEE"
else
  log "Checking all current assignees..."
  # Use process substitution instead of a pipe to avoid subshell issues
  while read -r user; do
    if [[ -n "$user" ]]; then
      check_user "$user"
    fi
  done < <(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json assignees --jq '.assignees[].login')
fi