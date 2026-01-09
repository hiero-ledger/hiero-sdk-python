#!/usr/bin/env bash
set -euo pipefail

#######################################
# Logging helper
#######################################
log() {
  echo "[advanced-check] $1"
}

#######################################
# Validate required environment variables
#######################################
if [[ -z "${REPO:-}" ]]; then
  log "ERROR: REPO must be set (e.g. owner/name)"
  exit 1
fi

OWNER="${REPO%%/*}"
NAME="${REPO##*/}"

#######################################
# GraphQL count helper (INTERMEDIATE ONLY)
#######################################
get_intermediate_count() {
  local user=$1

  gh api graphql -f query="
  {
    repository(owner: \"$OWNER\", name: \"$NAME\") {
      intermediate: issues(
        first: 1
        states: CLOSED
        filterBy: {
          assignee: \"$user\"
          labels: [\"intermediate\"]
        }
      ) {
        totalCount
      }
    }
  }"
}

#######################################
# Helper: has bot already commented for user?
#######################################
already_commented() {
  local user=$1

  gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
    --json comments \
    --jq --arg user "@$user" '
      .comments[].body
      | select(test("Hi " + $user + ", I cannot assign you to this issue yet."))
    ' | grep -q .
}

#######################################
# Helper: is user currently assigned?
#######################################
is_assigned() {
  local user=$1

  gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
    --json assignees \
    --jq --arg user "$user" '
      .assignees[].login | select(. == $user)
    ' | grep -q .
}

#######################################
# DRY RUN MODE
#######################################
if [[ "${DRY_RUN:-false}" == "true" ]]; then
  if [[ -z "${DRY_RUN_USER:-}" ]]; then
    log "ERROR: DRY_RUN_USER must be set when DRY_RUN=true"
    exit 1
  fi

  USER="$DRY_RUN_USER"
  log "DRY RUN MODE ENABLED"
  log "Repository: $REPO"
  log "User: @$USER"

  COUNTS=$(get_intermediate_count "$USER")
  INT_COUNT=$(jq '.data.repository.intermediate.totalCount' <<<"$COUNTS")

  echo
  log "Intermediate Issues (closed): $INT_COUNT"

  if (( INT_COUNT >= 1 )); then
    log "Result: USER QUALIFIED"
  else
    log "Result: USER NOT QUALIFIED"
  fi

  exit 0
fi

#######################################
# NORMAL MODE (ENFORCEMENT)
#######################################
if [[ -z "${ISSUE_NUMBER:-}" ]]; then
  log "ERROR: ISSUE_NUMBER must be set in normal mode"
  exit 1
fi

#######################################
# Check a single user
#######################################
check_user() {
  local user=$1
  log "Checking qualification for @$user..."

  # Permission exemption
  PERMISSION=$(
    gh api "repos/$REPO/collaborators/$user/permission" \
      --jq '.permission // "none"' 2>/dev/null || echo "none"
  )

  if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
    log "User @$user is core member ($PERMISSION). Skipping."
    return 0
  fi

  COUNTS=$(get_intermediate_count "$user")
  INT_COUNT=$(jq '.data.repository.intermediate.totalCount' <<<"$COUNTS")

  log "Counts → Intermediate: $INT_COUNT"

  if (( INT_COUNT >= 1 )); then
    log "User @$user qualified."
    return 0
  fi

  ###################################
  # Failure path (duplicate-safe)
  ###################################
  log "User @$user NOT qualified."

  SUGGESTION="[intermediate issues](https://github.com/$REPO/labels/intermediate)"

  MSG="Hi @$user, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase and require prior experience in this repository.

**Requirement:**
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please check out our **$SUGGESTION** to build your experience first!"

  if already_commented "$user"; then
    log "Comment already exists for @$user. Skipping comment."
  else
    log "Posting comment for @$user."
    gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
  fi

  if is_assigned "$user"; then
    log "Unassigning @$user."
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$user"
  else
    log "User @$user already unassigned. Skipping."
  fi
}

#######################################
# Main execution
#######################################
log "Normal enforcement mode enabled"
log "Repository: $REPO"
log "Issue: #$ISSUE_NUMBER"

if [[ -n "${TRIGGER_ASSIGNEE:-}" ]]; then
  check_user "$TRIGGER_ASSIGNEE"
else
  log "Checking all assignees..."

  ASSIGNEES=$(
    gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
      --json assignees --jq '.assignees[].login'
  )

  if [[ -z "$ASSIGNEES" ]]; then
    log "No assignees found."
    exit 0
  fi

  while read -r user; do
    [[ -n "$user" ]] && check_user "$user"
  done <<< "$ASSIGNEES"
fi
