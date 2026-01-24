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
echo " Repo:      $REPO"
echo " Threshold: $DAYS days"
echo " Dry Run:   $DRY_RUN"
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

  # Get assignment time (use the last assigned event)
  ASSIGN_TS=$(gh api "repos/$REPO/issues/$ISSUE/events" \
    --jq ".[] | select(.event==\"assigned\") | .created_at" \
    | tail -n1)

  if [ -z "$ASSIGN_TS" ]; then
    echo "[WARN] No assignment event found. Skipping."
    continue
  fi

  ASSIGN_TS_SEC=$(parse_ts "$ASSIGN_TS")
  DIFF_DAYS=$(( (NOW_TS - ASSIGN_TS_SEC) / 86400 ))

  echo "[INFO] Assigned at: $ASSIGN_TS"
  echo "[INFO] Days since assignment: $DIFF_DAYS"

  # Check if any open PRs are linked to this issue
  PR_NUMBERS=$(gh api \
    -H "Accept: application/vnd.github.mockingbird-preview+json" \
    "repos/$REPO/issues/$ISSUE/timeline" \
    --jq ".[] 
          | select(.event == \"cross-referenced\") 
          | select(.source.issue.pull_request != null) 
          | .source.issue.number" 2>/dev/null || true)

  OPEN_PR_FOUND=""
  if [ -n "$PR_NUMBERS" ]; then
    for PR_NUM in $PR_NUMBERS; do
      PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null || true)
      if [ "$PR_STATE" = "OPEN" ]; then
        OPEN_PR_FOUND="$PR_NUM"
        break
      fi
    done
  fi

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
If you are, please create a draft PR linked to this issue so we know you are working on it.
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