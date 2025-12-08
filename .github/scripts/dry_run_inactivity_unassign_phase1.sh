#!/usr/bin/env bash
set -euo pipefail

# ===============================================================
# DRY-RUN: Phase 1 Inactivity Unassign Bot
# - Uses assignment timestamp
# - Only considers OPEN PRs linked to the issue
# - Logs everything without making changes
# - Provides summary of users who would be unassigned
# ===============================================================

REPO="${REPO:-}"
DAYS="${DAYS:-21}"

if [ -z "$REPO" ]; then
  echo "ERROR: REPO environment variable not set. Example: export REPO=owner/repo"
  exit 1
fi

echo "------------------------------------------------------------"
echo " DRY RUN: Phase 1 Inactivity Unassign Check"
echo " Repo: $REPO"
echo " Threshold: $DAYS days"
echo "------------------------------------------------------------"
echo

NOW_TS=$(date +%s)

# -----------------------------
# Cross-platform timestamp parsing
# -----------------------------
parse_timestamp() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    date -d "$ts" +%s   # GNU date
  else
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"   # macOS/BSD
  fi
}

# -----------------------------
# Array to store summary of users to message
# -----------------------------
declare -a TO_UNASSIGN=()

# -----------------------------
# Fetch all open issues with assignees (skip PRs)
# -----------------------------
ISSUES=$(gh api "repos/$REPO/issues" \
  --paginate \
  --jq '.[] | select(.state=="open" and (.assignees | length > 0) and (.pull_request | not)) | .number')

if [ -z "$ISSUES" ]; then
  echo "No open issues with assignees found."
  exit 0
fi

echo "[INFO] Found issues: $ISSUES"
echo

# -----------------------------
# Iterate over issues
# -----------------------------
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

  # -----------------------------
  # Iterate over assignees
  # -----------------------------
  for USER in $ASSIGNEES; do
    echo "  → Checking assignee: $USER"

    # -----------------------------
    # Find the assignment timestamp for this user
    # -----------------------------
    ASSIGN_TS=$(gh api "repos/$REPO/issues/$ISSUE/events" \
      --jq ".[] | select(.event==\"assigned\" and .assignee.login==\"$USER\") | .created_at" | tail -n1)

    if [ -z "$ASSIGN_TS" ]; then
      echo "    [WARN] Could not find assignment timestamp. Using issue creation date as fallback."
      ASSIGN_TS=$(echo "$ISSUE_JSON" | jq -r '.created_at')
    fi

    ASSIGN_TS_SEC=$(parse_timestamp "$ASSIGN_TS")
    DIFF_DAYS=$(( (NOW_TS - ASSIGN_TS_SEC) / 86400 ))

    echo "    [INFO] Assigned at: $ASSIGN_TS"
    echo "    [INFO] Assigned for: $DIFF_DAYS days"

    # -----------------------------
    # Check if user has an OPEN PR linked to this issue
    # -----------------------------
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
      echo "    [KEEP] User $USER has an OPEN PR linked to this issue: $OPEN_PR_FOUND → skip unassign."
      echo
      continue
    fi

    echo "    [RESULT] User $USER has NO OPEN PRs linked to this issue."

    # -----------------------------
    # Decide on DRY-RUN unassign
    # -----------------------------
    if [ "$DIFF_DAYS" -ge "$DAYS" ]; then
    UNASSIGN_MESSAGE="Hi @$USER, you have been assigned to this issue for $DIFF_DAYS days without any open PRs linked. You would be automatically unassigned to keep things tidy. Please re-assign yourself if you are still working on this."

    echo "    [DRY RUN] Would UNASSIGN $USER (assigned for $DIFF_DAYS days, threshold $DAYS)"
    echo "    [DRY RUN] Message that would be posted:"
    echo "    --------------------------------------------------"
    echo "    $UNASSIGN_MESSAGE"
    echo "    --------------------------------------------------"

    TO_UNASSIGN+=("Issue #$ISSUE → $USER (assigned $DIFF_DAYS days) → Message: $UNASSIGN_MESSAGE")
    else
    echo "    [KEEP] Only $DIFF_DAYS days old → NOT stale yet."
    fi


    echo
  done

  echo
done

# -----------------------------
# Summary of all users to message
# -----------------------------
if [ ${#TO_UNASSIGN[@]} -gt 0 ]; then
  echo "============================================================"
  echo " SUMMARY: Users who would be unassigned / messaged"
  echo "============================================================"
  for ITEM in "${TO_UNASSIGN[@]}"; do
    echo "  - $ITEM"
  done
else
  echo "No users would be unassigned in this dry-run."
fi

echo "------------------------------------------------------------"
echo " DRY RUN COMPLETE — No changes were made."
echo "------------------------------------------------------------"
