#!/usr/bin/env bash
set -euo pipefail

# Env:
#   GH_TOKEN  - provided by GitHub Actions
#   REPO      - owner/repo (fallback to GITHUB_REPOSITORY)
#   DAYS      - reminder threshold in days (default 7)
#   DRY_RUN   - if "true", only log actions without posting comments

REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DAYS="${DAYS:-7}"
DRY_RUN="${DRY_RUN:-false}"
MARKER='<!-- issue-reminder-bot -->'

# Normalize DRY_RUN to "true" or "false"
if [[ "$DRY_RUN" == "true" || "$DRY_RUN" == "yes" || "$DRY_RUN" == "1" ]]; then
  DRY_RUN="true"
else
  DRY_RUN="false"
fi

if [ -z "$REPO" ]; then
  echo "ERROR: REPO environment variable not set."
  exit 1
fi

echo "------------------------------------------------------------"
echo " Issue Reminder Bot (No PR)"
echo " Repo:       $REPO"
echo " Threshold:  $DAYS days"
echo " Dry Run:    $DRY_RUN"
echo "------------------------------------------------------------"
echo

NOW_TS=$(date +%s)

# Cross-platform timestamp parsing (Linux + macOS/BSD)
parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    date -d "$ts" +%s      # GNU date (Linux)
  else
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"   # macOS/BSD
  fi
}

# Check for /working command from the specific user within the last X days
has_recent_working_command() {
  local issue_num="$1"
  local user="$2"
  local days_threshold="$3"

  local cutoff_ts=$((NOW_TS - (days_threshold * 86400)))
  local cutoff_iso
  if date --version >/dev/null 2>&1; then
    cutoff_iso=$(date -u -d "@$cutoff_ts" +"%Y-%m-%dT%H:%M:%SZ")
  else
    cutoff_iso=$(date -u -r "$cutoff_ts" +"%Y-%m-%dT%H:%M:%SZ")
  fi
  # Fetch recent comments only, filter for user and "/working" string
  local working_comments
  working_comments=$(gh api "repos/$REPO/issues/$issue_num/comments?since=$cutoff_iso" \
    --jq ".[] | select(.user.login == \"$user\") | select(.body | test(\"(^|\\\\s)/working(\\\\s|$)\"; \"i\")) | .created_at")

  if [[ -z "$working_comments" ]]; then
    return 1 # False
  fi

  # The 'since' parameter is an optimization, but the API may still return comments 
  # updated since the cutoff, not just created. We still need to check the create time.
  for created_at in $working_comments; do
    local comment_ts
    comment_ts=$(parse_ts "$created_at")
    if (( comment_ts >= cutoff_ts )); then
      return 0 # True
    fi
  done

  return 1 # False
}

# Fetch open ISSUES (not PRs) that have assignees
ALL_ISSUES_JSON=$(gh api "repos/$REPO/issues" \
  --paginate \
  --jq '.[] | select(.state=="open" and (.assignees | length > 0) and (.pull_request | not))')

if [ -z "$ALL_ISSUES_JSON" ]; then
  echo "No open issues with assignees found."
  exit 0
fi

echo "$ALL_ISSUES_JSON" | jq -c '.' | while read -r ISSUE_JSON; do
  ISSUE=$(echo "$ISSUE_JSON" | jq -r '.number')
  echo "============================================================"
  echo " ISSUE #$ISSUE"
  echo "============================================================"

  ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login')

  if [ -z "$ASSIGNEES" ]; then
    echo "[INFO] No assignees? Skipping."
    echo
    continue
  fi

  echo "[INFO] Assignees: $ASSIGNEES"
  echo

  # Check if this issue already has a reminder comment from ReminderBot
  EXISTING_COMMENT=$(gh api "repos/$REPO/issues/$ISSUE/comments" \
    --jq ".[] | select(.user.login == \"github-actions[bot]\") | select(.body | contains(\"<!-- issue-reminder-bot -->\")) | .id" \
    | head -n1)

  if [ -n "$EXISTING_COMMENT" ]; then
    echo "[INFO] Reminder comment already posted on this issue."
    echo
    continue
  fi

  # Immunity Check: If ANY assignee has said /working, we skip the reminder for the whole issue
  SKIP_REMINDER=false
  for USER in $ASSIGNEES; do
    if has_recent_working_command "$ISSUE" "$USER" "$DAYS"; then
      echo "[SKIP] User @$USER posted '/working' recently. Skipping reminder."
      SKIP_REMINDER=true
      break
    fi
  done

  if [ "$SKIP_REMINDER" = "true" ]; then
    continue
  fi

  # Get assignment time (use the last assigned event)
  if ! ASSIGN_TS=$(gh api graphql -f query="
  query {
    repository(owner: \"${REPO%/*}\", name: \"${REPO#*/}\") {
      issue(number: $ISSUE) {
        timelineItems(itemTypes: [ASSIGNED_EVENT], last: 1) {
          nodes {
            ... on AssignedEvent {
              createdAt
              assignee {
                __typename
                ... on User { login }
              }
            }
          }
        }
      }
    }
  }
" --jq '.data.repository.issue.timelineItems.nodes[0].createdAt' 2>&1); then
    echo "[WARN] GraphQL query failed for issue #$ISSUE: $ASSIGN_TS. Skipping."
    continue
  fi

  if [ -z "$ASSIGN_TS" ] || [ "$ASSIGN_TS" = "null" ]; then
    echo "[WARN] No assignment event found for issue #$ISSUE. Skipping."
    continue
  fi

  ASSIGN_TS_SEC=$(parse_ts "$ASSIGN_TS")
  DIFF_DAYS=$(( (NOW_TS - ASSIGN_TS_SEC) / 86400 ))

  echo "[INFO] Assigned at: $ASSIGN_TS"
  echo "[INFO] Days since assignment: $DIFF_DAYS"

  # Check if any open PRs are linked to this issue
  OPEN_PR_FOUND=$(gh api graphql -f query="
    query {
      repository(owner: \"${REPO%/*}\", name: \"${REPO#*/}\") {
        issue(number: $ISSUE) {
          closedByPullRequestsReferences(first: 100, includeClosedPrs: false) {
            nodes { number state }
          }
        }
      }
    }
  " --jq '[.data.repository.issue.closedByPullRequestsReferences.nodes[] | select(.state == "OPEN") | .number] | first // empty' 2>&1) || true

  if [ -n "$OPEN_PR_FOUND" ]; then
    echo "[KEEP] An OPEN PR #$OPEN_PR_FOUND is linked to this issue → skip reminder."
    echo
    continue
  fi

  echo "[RESULT] No OPEN PRs linked to this issue."

  # Check if threshold has been reached
  if [ "$DIFF_DAYS" -lt "$DAYS" ]; then
    echo "[WAIT] Only $DIFF_DAYS days (< $DAYS) → not yet time for reminder."
    echo
    continue
  fi

  echo "[REMIND] Issue #$ISSUE assigned for $DIFF_DAYS days, posting reminder."

  ASSIGNEE_MENTIONS=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login | "@" + .' | xargs)

  MESSAGE="${MARKER}
Hi ${ASSIGNEE_MENTIONS} 👋

This issue has been assigned but no pull request has been created yet.
Are you still planning on working on it?
If you are, please create a draft PR linked to this issue or comment \`/working\` to let us know.
If you’re no longer able to work on this issue, you can comment \`/unassign\` to release it.

From the Python SDK Team"

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY RUN] Would post comment on issue #$ISSUE:"
    echo "$MESSAGE"
  else
    gh issue comment "$ISSUE" --repo "$REPO" --body "$MESSAGE"
    echo "[DONE] Posted reminder comment on issue #$ISSUE."
  fi
  echo
done

echo "------------------------------------------------------------"
echo " Issue Reminder Bot (No PR) complete."
echo "------------------------------------------------------------"
