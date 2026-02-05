#!/usr/bin/env bash
set -euo pipefail

#######################################
# Logging helper
#######################################
log() {
  echo "[advanced-check] $1"
}

#######################################
# Configuration
#######################################
REQUIRED_INTERMEDIATE_COUNT=1

#######################################
# Validate required environment variables
#######################################
if [[ -z "${REPO:-}" ]]; then
  log "ERROR: REPO must be set (e.g. owner/name)"
  exit 1
fi

# gh CLI authentication is required in both DRY_RUN and normal mode
if [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  log "ERROR: GH_TOKEN (or GITHUB_TOKEN) must be set for gh CLI authentication"
  exit 1
fi

OWNER="${REPO%%/*}"
NAME="${REPO##*/}"

#######################################
# Constants
#######################################
COMMENT_MARKER_PREFIX="<!-- advanced-check:unqualified -->"

#######################################
# Validation helpers
#######################################
validate_username() {
  local user=$1
  # GitHub usernames:
  #  - 1–39 characters
  #  - alphanumeric or single hyphens
  #  - no leading/trailing hyphen
  #  - no consecutive hyphens
  #if [[ ! "$user" =~ ^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$ ]]; then old line
  if [[ ! "$user" =~ ^[A-Za-z0-9]([A-Za-z0-9]|-){0,38}$ ]]; then
    log "ERROR: Invalid GitHub username: '$user'"
    return 1
  fi
}

# Trim whitespace/newlines/carriage returns from username
trim_username() {
  local user="$1"
  echo -n "$user" | tr -d '[:space:]\r'
}

#######################################
# GraphQL count helper (INTERMEDIATE ONLY)
#######################################
get_intermediate_count() {
  local user=$1
  validate_username "$user"

  gh api graphql \
    -f query='
      query($owner: String!, $name: String!, $user: String!) {
        repository(owner: $owner, name: $name) {
          intermediate: issues(
            first: 1
            states: CLOSED
            filterBy: { assignee: $user, labels: ["intermediate"] }
          ) {
            totalCount
          }
        }
      }' \
    -f owner="$OWNER" \
    -f name="$NAME" \
    -f user="$user"
}

#######################################
# Helper: has bot already commented for user?
#######################################
already_commented() {
  local user=$1
  local marker="$COMMENT_MARKER_PREFIX @$user"
  gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
    --json comments \
    --jq '.comments[].body' | grep -Fq "$marker"
}

#######################################
# Helper: is user currently assigned?
#######################################

is_assigned() {
  local user=$1
  gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
    --json assignees \
    --jq '.assignees[].login' | grep -Fxq "$user"
}

#######################################
# DRY RUN MODE
#######################################
if [[ "${DRY_RUN:-false}" == "true" ]]; then
  if [[ -z "${DRY_RUN_USER:-}" ]]; then
    log "ERROR: DRY_RUN_USER must be set when DRY_RUN=true"
    exit 1
  fi

  # Trim first
  USER="$(trim_username "$DRY_RUN_USER")"

  # DEBUG logs BEFORE validation
  log "DRY RUN MODE ENABLED"
  log "Repository: $REPO"
  log "DRY_RUN_USER raw='$DRY_RUN_USER'"
  log "DEBUG: USER after trim='$USER'"

  # Validate after logging
  validate_username "$USER"

  log "User: @$USER"

  COUNTS=$(get_intermediate_count "$USER")
  INT_COUNT=$(jq '.data.repository.intermediate.totalCount' <<<"$COUNTS")

  echo
  log "Intermediate Issues (closed): $INT_COUNT"

  if (( INT_COUNT >= REQUIRED_INTERMEDIATE_COUNT )); then
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
  user="$(trim_username "$user")"
  validate_username "$user"

  log "Checking qualification for @$user..."

  # Permission exemption
  PERMISSION=$(
    gh api "repos/$REPO/collaborators/$user/permission" \
      --jq '.permission // "none"' 2>/dev/null || echo "none"
  )

  if [[ "$PERMISSION" =~ ^(admin|maintain|write|triage)$ ]]; then
    log "User @$user is core member ($PERMISSION). Skipping."
    return 0
  fi

  COUNTS=$(get_intermediate_count "$user")
  INT_COUNT=$(jq '.data.repository.intermediate.totalCount' <<<"$COUNTS")

  log "Counts → Intermediate: $INT_COUNT"

  if (( INT_COUNT >= REQUIRED_INTERMEDIATE_COUNT )); then
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
- Complete at least **$REQUIRED_INTERMEDIATE_COUNT** 'intermediate' issue (You have: **$INT_COUNT**)

Please check out our **$SUGGESTION** to build your experience first!

$COMMENT_MARKER_PREFIX @$user"

  if already_commented "$user"; then
    log "Comment already exists for @$user. Skipping comment."
  else
    log "Posting comment for @$user."
    gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
  fi

  if is_assigned "$user"; then
  log "Unassigning @$user ..."
  json_body="{\"assignees\": [\"$user\"]}"
  response=$(
    gh api \
      --method DELETE \
      "repos/$REPO/issues/$ISSUE_NUMBER/assignees" \
      --input <(echo "$json_body") \
      || echo "error"
    )
    if [[ "$response" != "error" ]]; then
      log "Successfully unassigned @$user."
    else
      log "Failed to unassign @$user."
    fi
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
      --json assignees \
      --jq '.assignees[].login'
  )

  if [[ -z "$ASSIGNEES" ]]; then
    log "No assignees found."
    exit 0
  fi

  while read -r user; do
    [[ -n "$user" ]] && check_user "$user"
  done <<< "$ASSIGNEES"
fi
