#!/usr/bin/env bash
set -euo pipefail

# Env:
#   GH_TOKEN  - provided by GitHub Actions
#   REPO      - owner/repo (fallback to GITHUB_REPOSITORY)
#   DAYS      - inactivity threshold in days (default 21)

REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DAYS="${DAYS:-21}"

if [ -z "$REPO" ]; then
  echo "ERROR: REPO environment variable not set."
  exit 1
fi

echo "------------------------------------------------------------"
echo " Inactivity Unassign Bot (Phase 1)"
echo " Repo:      $REPO"
echo " Threshold: $DAYS days"
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
ISSUES=$(gh api "repos/$REPO/issues" \
  --paginate \
  --jq '.[] | select(.state=="open" and (.assignees | length > 0) and (.pull_request | not)) | .number')

if [ -z "$ISSUES" ]; then
  echo "No open issues with assignees found."
  exit 0
fi

for ISSUE in $ISSUES; do
  echo "============================================================"
  echo " ISSUE #$ISSUE"
  echo "============================================================"

  ISSUE_JSON=$(gh api "repos/$REPO/issues/$ISSUE")
  ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login')

  if [ -z "$ASSIGNEES" ]; then
    echo "[INFO] No assignees? Skipping."
    echo
    continue
  fi

  echo "[INFO] Assignees: $ASSIGNEES"
  echo

  for USER in $ASSIGNEES; do
    echo "  → Checking assignee: $USER"

    # 1) Find when THIS USER was last assigned to THIS ISSUE
    ASSIGN_TS=$(gh api "repos/$REPO/issues/$ISSUE/events" \
      --jq ".[] | select(.event==\"assigned\" and .assignee.login==\"$USER\") | .created_at" \
      | tail -n1)

    if [ -z "$ASSIGN_TS" ]; then
      echo "    [WARN] No assignment event for $USER, falling back to issue creation."
      ASSIGN_TS=$(echo "$ISSUE_JSON" | jq -r '.created_at')
    fi

    ASSIGN_TS_SEC=$(parse_ts "$ASSIGN_TS")
    DIFF_DAYS=$(( (NOW_TS - ASSIGN_TS_SEC) / 86400 ))

    echo "    [INFO] Assigned at: $ASSIGN_TS"
    echo "    [INFO] Assigned for: $DIFF_DAYS days"

    # 2) Check for OPEN PRs linked to THIS ISSUE by THIS USER (via timeline)
    PR_NUMBERS=$(gh api \
      -H "Accept: application/vnd.github.mockingbird-preview+json" \
      "repos/$REPO/issues/$ISSUE/timeline" \
      --jq ".[] 
            | select(.event == \"cross-referenced\") 
            | select(.source.issue.pull_request != null) 
            | select(.source.issue.user.login == \"$USER\") 
            | .source.issue.number")

    OPEN_PR_FOUND=""
    for PR_NUM in $PR_NUMBERS; do
      PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state')
      if [ "$PR_STATE" = "OPEN" ]; then
        OPEN_PR_FOUND="$PR_NUM"
        break
      fi
    done

    if [ -n "$OPEN_PR_FOUND" ]; then
      echo "    [KEEP] $USER has OPEN PR #$OPEN_PR_FOUND linked to this issue → skip unassign."
      echo
      continue
    fi

    echo "    [RESULT] $USER has NO OPEN PRs linked to this issue."

    # 3) Decide unassign
    if [ "$DIFF_DAYS" -lt "$DAYS" ]; then
      echo "    [KEEP] Only $DIFF_DAYS days (< $DAYS) → not stale yet."
      echo
      continue
    fi

    echo "    [UNASSIGN] $USER (assigned $DIFF_DAYS days, threshold $DAYS)"

    # Unassign via gh CLI helper
    gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"

    # Comment
    MESSAGE="Hi @$USER, you were automatically unassigned from this issue because there have been no open PRs linked to it for **$DIFF_DAYS days**. This helps keep issues available for contributors who are currently active. You're very welcome to re-assign yourself or pick this back up whenever you have time 🚀"

    gh issue comment "$ISSUE" --repo "$REPO" --body "$MESSAGE"

    echo "    [DONE] Unassigned and commented on issue #$ISSUE for $USER."
    echo
  done

  echo
done

echo "------------------------------------------------------------"
echo " Inactivity Unassign Bot (Phase 1) complete."
echo "------------------------------------------------------------"