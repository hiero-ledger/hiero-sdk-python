#!/bin/bash
set -euo pipefail

# Function to check a single user
check_user() {
  local user=$1
  echo "Checking qualification for @$user..."

  # 1. Permission exemption
  PERM_JSON=$(gh api "repos/$REPO/collaborators/$user/permission" 2>/dev/null || echo '{"permission":"none"}')
  PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission // "none"')

  if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
    echo "User @$user is a core member ($PERMISSION). Qualification check skipped."
    return 0
  fi

  # 2. Get counts
  GFI_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"good first issue\""
  INT_QUERY="repo:$REPO is:issue is:closed assignee:$user -reason:\"not planned\" label:\"intermediate\""

  GFI_COUNT=$(gh api "search/issues" -f q="$GFI_QUERY" --jq '.total_count' || echo "0")
  INT_COUNT=$(gh api "search/issues" -f q="$INT_QUERY" --jq '.total_count' || echo "0")

  if ! [[ "$GFI_COUNT" =~ ^[0-9]+$ ]]; then GFI_COUNT=0; fi
  if ! [[ "$INT_COUNT" =~ ^[0-9]+$ ]]; then INT_COUNT=0; fi

  # 3. Validation Logic
  if (( GFI_COUNT >= 1 )) && (( INT_COUNT >= 1 )); then
    echo "User @$user qualified."
    return 0
  else
    echo "User @$user failed. Unassigning..."

    # CodeRabbit Improvement: Tailor the suggestion based on what is missing
    if (( GFI_COUNT == 0 )); then
      SUGGESTION="[good first issue](https://github.com/$REPO/labels/good%20first%20issue)"
    else
      SUGGESTION="[intermediate issue](https://github.com/$REPO/labels/intermediate)"
    fi

    # Remove the user
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$user"

    # Post the tailored message
    MSG="Hi @$user, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase. They require significant testing and can impact automation and CI behavior.

**Requirement:**
- Complete at least **1** 'good first issue' (You have: **$GFI_COUNT**)
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please check out our **$SUGGESTION** tasks to build your experience first!"

    gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
  fi
}

# --- Main Logic ---

# Define a simple log function so the script doesn't crash
log() {
  echo "[advanced-check] $1"
}

# If TRIGGER_ASSIGNEE is set (from 'assigned' event), check just that person.
# Otherwise (from 'labeled' event), check EVERYONE currently assigned.
if [[ -n "${TRIGGER_ASSIGNEE:-}" ]]; then
  check_user "$TRIGGER_ASSIGNEE"
else
  log "Checking all current assignees..."
  # Fetch all current assignees using GitHub CLI
  ASSIGNEES=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json assignees --jq '.assignees[].login')
  
  for user in $ASSIGNEES; do
    check_user "$user"
  done
fi