#!/usr/bin/env bash
set -euo pipefail

# Unified Inactivity Bot (Phase 1 + Phase 2)
# Supports DRY_RUN mode:
#   DRY_RUN = 1 → simulate only (no changes)
#   DRY_RUN = 0 → real actions

REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DAYS="${DAYS:-21}"
DRY_RUN="${DRY_RUN:-0}"

# Normalize DRY_RUN input ("true"/"false" → 1/0)
shopt -s nocasematch
case "$DRY_RUN" in
  "true")  DRY_RUN=1 ;;
  "false") DRY_RUN=0 ;;
esac
shopt -u nocasematch

if [[ -z "$REPO" ]]; then
  echo "ERROR: REPO environment variable not set."
  exit 1
fi

echo "------------------------------------------------------------"
echo " Unified Inactivity Unassign Bot"
echo " Repo:      $REPO"
echo " Threshold: $DAYS days"
echo " DRY_RUN:   $DRY_RUN"
echo "------------------------------------------------------------"

NOW_TS=$(date +%s)

# Converts GitHub timestamps → epoch
parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    date -d "$ts" +%s
  else
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"
  fi
}

# Fetch all open issues that have assignees
ISSUES=$(
  gh api "repos/$REPO/issues" --paginate \
    --jq '.[] 
      | select(.state=="open" and (.assignees|length>0) and (.pull_request|not))
      | .number'
)

for ISSUE in $ISSUES; do
  echo "============================================================"
  echo " ISSUE #$ISSUE"
  echo "============================================================"

  ISSUE_JSON=$(gh api "repos/$REPO/issues/$ISSUE")
  ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login')
  CREATED_AT=$(echo "$ISSUE_JSON" | jq -r '.created_at')
  CREATED_TS=$(parse_ts "$CREATED_AT")

  for USER in $ASSIGNEES; do
    echo "  → Checking assignee: $USER"

    # Fetch timeline (for PR cross-references)
    TIMELINE=$(gh api \
      -H "Accept: application/vnd.github.mockingbird-preview+json" \
      "repos/$REPO/issues/$ISSUE/timeline"
    )

    # Filter only PRs from SAME repository
    PR_NUMBERS=$(echo "$TIMELINE" | jq -r --arg repo "$REPO" '
      .[]
      | select(.event == "cross-referenced")
      | select(.source.issue.pull_request != null)
      | select(.source.issue.repository.full_name == $repo)
      | .source.issue.number
    ')

    # -------------------------------
    # PHASE 1: ISSUE HAS NO PR
    # -------------------------------
    if [[ -z "$PR_NUMBERS" ]]; then
      AGE_DAYS=$(( (NOW_TS - CREATED_TS) / 86400 ))
      echo "    [INFO] Assigned for: ${AGE_DAYS} days"

      if (( AGE_DAYS >= DAYS )); then
        echo "    [PHASE 1 STALE] No PR linked + stale"

        if (( DRY_RUN == 0 )); then
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"
          echo "    [ACTION] Unassigned $USER"
        else
          echo "    [DRY RUN] Would unassign $USER"
        fi
      else
        echo "    [KEEP] Not stale yet"
      fi

      continue
    fi

    # -------------------------------
    # PHASE 2: ISSUE HAS PR(s)
    # -------------------------------
    echo "    [INFO] Linked PRs: $PR_NUMBERS"

    for PR_NUM in $PR_NUMBERS; do

      # Safe PR check
      if ! PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null); then
        echo "    [SKIP] #$PR_NUM is not a valid PR in $REPO"
        continue
      fi

      if [[ "$PR_STATE" != "OPEN" ]]; then
        echo "    [SKIP] PR #$PR_NUM is not open"
        continue
      fi

      # Last commit (paginate + last)
      COMMITS=$(gh api "repos/$REPO/pulls/$PR_NUM/commits" --paginate)
      LAST_TS_STR=$(echo "$COMMITS" | jq -r 'last | (.commit.committer.date // .commit.author.date)')
      LAST_TS=$(parse_ts "$LAST_TS_STR")

      AGE_DAYS=$(( (NOW_TS - LAST_TS) / 86400 ))

      echo "    [INFO] PR #$PR_NUM → Last commit = $LAST_TS_STR (~${AGE_DAYS} days)"

      if (( AGE_DAYS >= DAYS )); then
        echo "    [STALE PR] PR #$PR_NUM is stale"

        if (( DRY_RUN == 0 )); then
          gh pr close "$PR_NUM" --repo "$REPO"
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"
          echo "    [ACTION] Closed PR + unassigned $USER"
        else
          echo "    [DRY RUN] Would close PR #$PR_NUM + unassign $USER"
        fi
      else
        echo "    [KEEP] PR is active"
      fi

    done

  done

done

echo "------------------------------------------------------------"
echo " Unified Inactivity Bot Complete"
echo " DRY_RUN: $DRY_RUN"
echo "------------------------------------------------------------"
