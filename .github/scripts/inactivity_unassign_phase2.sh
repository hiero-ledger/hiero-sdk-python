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
echo " Inactivity Unassign Bot (Phase 2 - PR inactivity)"
echo " Repo:      $REPO"
echo " Threshold: $DAYS days (no commit activity on PR)"
echo "------------------------------------------------------------"

NOW_TS=$(date +%s)

# Cross-platform timestamp parsing (Linux + macOS/BSD)
parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    # GNU date (Linux)
    date -d "$ts" +%s
  else
    # macOS / BSD
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"
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

    # Find OPEN PRs linked to THIS issue, authored by THIS user
    PR_NUMBERS=$(gh api \
      -H "Accept: application/vnd.github.mockingbird-preview+json" \
      "repos/$REPO/issues/$ISSUE/timeline" \
      --jq ".[] 
        | select(.event == \"cross-referenced\") 
        | select(.source.issue.pull_request != null) 
        | select(.source.issue.user.login == \"$USER\") 
        | .source.issue.number")

    if [ -z "$PR_NUMBERS" ]; then
      echo "    [INFO] No linked PRs by $USER for this issue → Phase 1 covers the no-PR case."
      echo
      continue
    fi

    echo "    [INFO] Linked PRs by $USER: $PR_NUMBERS"

    STALE_PR=""
    STALE_AGE_DAYS=0

    # Look for a stale OPEN PR
    for PR_NUM in $PR_NUMBERS; do
      PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state')

      if [ "$PR_STATE" != "OPEN" ]; then
        echo "    [SKIP] PR #$PR_NUM is not open ($PR_STATE)."
        continue
      fi

      # Last commit date on the PR: pick the truly latest by timestamp
      COMMITS_JSON=$(gh api "repos/$REPO/pulls/$PR_NUM/commits" --paginate 2>/dev/null || echo "[]")

      LAST_COMMIT_DATE=$(echo "$COMMITS_JSON" \
        | jq -r '
            select(length > 0)
            | max_by(.commit.committer.date // .commit.author.date)
            | (.commit.committer.date // .commit.author.date)
          ')

      if [ -z "$LAST_COMMIT_DATE" ] || [ "$LAST_COMMIT_DATE" = "null" ]; then
        echo "    [WARN] Could not determine last commit date for PR #$PR_NUM, skipping."
        continue
      fi

      LAST_COMMIT_TS=$(parse_ts "$LAST_COMMIT_DATE")
      AGE_DAYS=$(( (NOW_TS - LAST_COMMIT_TS) / 86400 ))

      echo "    [INFO] PR #$PR_NUM last commit: $LAST_COMMIT_DATE (~${AGE_DAYS} days ago)"

      if [ "$AGE_DAYS" -ge "$DAYS" ]; then
        STALE_PR="$PR_NUM"
        STALE_AGE_DAYS="$AGE_DAYS"
        break
      fi
    done

    if [ -z "$STALE_PR" ]; then
      echo "    [KEEP] No OPEN PR for $USER is stale (>= $DAYS days)."
      echo
      continue
    fi

    echo "    [STALE] PR #$STALE_PR by $USER has had no commit activity for $STALE_AGE_DAYS days (>= $DAYS)."
    echo "    [ACTION] Closing PR #$STALE_PR and unassigning @$USER from issue #$ISSUE."

    MESSAGE=$(
      cat <<EOF
Hi @$USER, this is InactivityBot.

This pull request has become stale, with no development activity for **$STALE_AGE_DAYS days**. As a result, we have closed this pull request and unassigned you from the linked issue to keep the backlog available for active contributors.

You are welcome to get assigned to an issue once again once you have capacity.

In the future, please close old pull requests that will not have development activity and request to be unassigned if you are no longer working on the issue.
EOF
    )

    # Comment on the PR
    gh pr comment "$STALE_PR" --repo "$REPO" --body "$MESSAGE"
    echo "    [DONE] Commented on PR #$STALE_PR."

    # Close the PR
    gh pr close "$STALE_PR" --repo "$REPO"
    echo "    [DONE] Closed PR #$STALE_PR."

    # Unassign the user from the issue
    gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"
    echo "    [DONE] Unassigned @$USER from issue #$ISSUE."
    echo
  done

  echo
done

echo "------------------------------------------------------------"
echo " Inactivity Unassign Bot (Phase 2) complete."
echo "------------------------------------------------------------"
