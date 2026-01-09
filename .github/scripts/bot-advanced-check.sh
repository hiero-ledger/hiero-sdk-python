#!/bin/bash
set -euo pipefail

# 1. Define Helper Functions First
log() {
  echo "[advanced-check] $1"
}

# 2. Validate required environment variables
if [[ -z "${REPO:-}" ]] || [[ -z "${ISSUE_NUMBER:-}" ]] || [[ -z "${GH_TOKEN:-}" ]]; then
  log "ERROR: Required environment variables (REPO, ISSUE_NUMBER, GH_TOKEN) must be set"
  exit 1
fi

# 3. Function to check a single user
check_user() {
  local user=$1
  log "Checking qualification for @$user..."

  # Permission exemption
  PERM_JSON=$(gh api "repos/$REPO/collaborators/$user/permission" 2>/dev/null || echo '{"permission":"none"}')
  PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission // "none"')

  if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
    log "User @$user is core member ($PERMISSION). Qualification check skipped."
    return 0
  fi

  # 2. Get counts
  # Using exact repository label names ("Good First Issue" and "intermediate")
  GFI_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"Good First Issue\""
  INT_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"intermediate\""

  GFI_COUNT=$(gh api "search/issues" -f q="$GFI_QUERY" --jq '.total_count' || echo "0")
  INT_COUNT=$(gh api "search/issues" -f q="$INT_QUERY" --jq '.total_count' || echo "0")

  # Numeric validation
  if ! [[ "$GFI_COUNT" =~ ^[0-9]+$ ]]; then GFI_COUNT=0; fi
  if ! [[ "$INT_COUNT" =~ ^[0-9]+$ ]]; then INT_COUNT=0; fi

  # Validation Logic
  if (( GFI_COUNT >= 1 )) && (( INT_COUNT >= 1 )); then
    log "User @$user qualified."
    return 0
  else
    log "User @$user failed. Unassigning..."

    # Tailor the suggestion based on what is missing
    # Links and names now match exact repository labels
    if (( GFI_COUNT == 0 )); then
      SUGGESTION="[Good First Issue](https://github.com/$REPO/labels/Good%20First%20Issue)"
    else
      SUGGESTION="[intermediate issue](https://github.com/$REPO/labels/intermediate)"
    fi

    # Post the message FIRST, then unassign.
    MSG="Hi @$user, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase. They require significant testing and can impact automation and CI behavior.

**Requirement:**
- Complete at least **1** 'Good First Issue' (You have: **$GFI_COUNT**)
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please check out our **$SUGGESTION** tasks to build your experience first!"

    gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$user"
  fi
}

# --- Main Logic ---

if [[ -n "${TRIGGER_ASSIGNEE:-}" ]]; then
  check_user "$TRIGGER_ASSIGNEE"
else
  log "Checking all current assignees..."
  
  # Fetch assignees into a variable first. 
  ASSIGNEE_LIST=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json assignees --jq '.assignees[].login')

  if [[ -z "$ASSIGNEE_LIST" ]]; then
    log "No assignees found to check."
  else
    # Use a here-string (<<<) to iterate over the variable safely.
    while read -r user; do
      if [[ -n "$user" ]]; then
        check_user "$user"
      fi
    done <<< "$ASSIGNEE_LIST"
  fi
fi