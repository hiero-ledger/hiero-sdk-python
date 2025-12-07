#!/usr/bin/env bash
set -euo pipefail

# DRY-RUN: Phase 2 Inactivity Unassign Bot
# - Does NOT change anything
# - Logs which PRs/issues WOULD be affected

REPO="${REPO:-}"
DAYS="${DAYS:-21}"

if [ -z "$REPO" ]; then
  echo "ERROR: REPO environment variable not set."
  echo "Example: export REPO=owner/repo"
  exit 1
fi

echo "------------------------------------------------------------"
echo " DRY RUN: Phase 2 Inactivity Unassign (PR inactivity)"
echo " Repo:      $REPO"
echo " Threshold: $DAYS days (no commit activity on PR)"
echo "------------------------------------------------------------"

NOW_TS=$(date +%s)

parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    date -d "$ts" +%s
  else
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"
  fi
}

declare -a SUMMARY=()

ISSUES=$(gh api "repos/$REPO/issues" \
  --paginate \
  --jq '.[] | select(.state=="open" and (.assignees | length > 0) and (.pull_request | not)) | .number')

if [ -z "$ISSUES" ]; then
  echo "No open issues with assignees found."
  exit 0
fi

echo "[INFO] Found issues: $ISSUES"
echo

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

    PR_NUMBERS=$(gh api \
      -H "Accept: application/vnd.github.mockingbird-preview+json" \
      "repos/$REPO/issues/$ISSUE/timeline" \
      --jq ".[] 
        | select(.event == \"cross-referenced\") 
        | select(.source.issue.pull_request != null) 
        | select(.source.issue.user.login == \"$USER\") 
        | .source.issue.number")

    if [ -z "$PR_NUMBERS" ]; then
      echo "    [INFO] No linked PRs by $USER for this issue."
      echo
      continue
    fi

    echo "    [INFO] Linked PRs by $USER: $PR_NUMBERS"

    STALE_PR=""
    STALE_AGE_DAYS=0

    for PR_NUM in $PR_NUMBERS; do
      PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state')

      if [ "$PR_STATE" != "OPEN" ]; then
        echo "    [SKIP] PR #$PR_NUM is not open ($PR_STATE)."
        continue
      fi

      LAST_COMMIT_DATE=$(gh api "repos/$REPO/pulls/$PR_NUM/commits" \
        --jq '.[-1].commit.committer.date // .[-1].commit.author.date' 2>/dev/null || echo "")

      if [ -z "$LAST_COMMIT_DATE" ]; then
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

    echo "    [DRY RUN] Would CLOSE PR #$STALE_PR (no commits for $STALE_AGE_DAYS days)"
    echo "    [DRY RUN] Would UNASSIGN @$USER from issue #$ISSUE"
    echo

    SUMMARY+=("Issue #$ISSUE → user @$USER → stale PR #$STALE_PR (no commits for $STALE_AGE_DAYS days)")
  done

  echo
done

if [ ${#SUMMARY[@]} -gt 0 ]; then
  echo "============================================================"
  echo " SUMMARY: Actions that WOULD be taken (no changes made)"
  echo "============================================================"
  for ITEM in "${SUMMARY[@]}"; do
    echo " - $ITEM"
  done
else
  echo "No stale PRs / unassignments detected in this dry-run."
fi

echo "------------------------------------------------------------"
echo " DRY RUN COMPLETE — No changes were made."
echo "------------------------------------------------------------"
