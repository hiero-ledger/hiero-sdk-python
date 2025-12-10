#!/usr/bin/env bash
set -euo pipefail

# Unified Inactivity Bot (Phase 1 + Phase 2)
# DRY_RUN:
#   1 → simulate only (no changes)
#   0 → real actions

REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DAYS="${DAYS:-21}"
DRY_RUN="${DRY_RUN:-0}"

# Normalise DRY_RUN input ("true"/"false" → 1/0, case-insensitive)
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

# Convert GitHub timestamp → unix epoch
parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    # GNU date
    date -d "$ts" +%s
  else
    # macOS / BSD
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"
  fi
}

# Fetch all open issues with assignees (non-PRs)
ISSUES=$(
  gh api "repos/$REPO/issues" --paginate \
    --jq '.[] 
      | select(.state=="open" and (.assignees|length>0) and (.pull_request|not))
      | .number'
)

if [[ -z "$ISSUES" ]]; then
  echo "[INFO] No open issues with assignees found."
fi

for ISSUE in $ISSUES; do
  echo "============================================================"
  echo " ISSUE #$ISSUE"
  echo "============================================================"

  ISSUE_JSON=$(gh api "repos/$REPO/issues/$ISSUE")
  ISSUE_CREATED_AT=$(echo "$ISSUE_JSON" | jq -r '.created_at')
  ISSUE_CREATED_TS=$(parse_ts "$ISSUE_CREATED_AT")

  ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login')

  echo "  [INFO] Issue created at: $ISSUE_CREATED_AT"

  # Fetch timeline once per issue (used for assignment + PR links)
  TIMELINE=$(gh api \
    -H "Accept: application/vnd.github.mockingbird-preview+json" \
    "repos/$REPO/issues/$ISSUE/timeline"
  )

  for USER in $ASSIGNEES; do
    echo
    echo "  → Checking assignee: $USER"

    # -------------------------------
    # Determine assignment time for USER
    # -------------------------------
    ASSIGNED_AT_STR=$(
      echo "$TIMELINE" | jq -r --arg user "$USER" '
        [ .[]
          | select(.event=="assigned" and .assignee.login==$user)
          | .created_at
        ] 
        | sort 
        | last // "null"
      '
    )

    ASSIGNMENT_SOURCE="assignment_event"

    if [[ -z "$ASSIGNED_AT_STR" || "$ASSIGNED_AT_STR" == "null" ]]; then
      # Fallback: no explicit assignment event -> use issue creation time
      ASSIGNED_AT_STR="$ISSUE_CREATED_AT"
      ASSIGNMENT_SOURCE="issue_created_at (no explicit assignment event)"
    fi

    ASSIGNED_TS=$(parse_ts "$ASSIGNED_AT_STR")
    ASSIGNED_AGE_DAYS=$(( (NOW_TS - ASSIGNED_TS) / 86400 ))

    echo "    [INFO] Assignment source: $ASSIGNMENT_SOURCE"
    echo "    [INFO] Assigned at:      $ASSIGNED_AT_STR (~${ASSIGNED_AGE_DAYS} days ago)"

    # -------------------------------
    # Find linked PRs for THIS user in THIS repo
    # -------------------------------
    PR_NUMBERS=$(
      echo "$TIMELINE" | jq -r --arg repo "$REPO" --arg user "$USER" '
        .[]
        | select(.event == "cross-referenced")
        | select(.source.issue.pull_request != null)
        | select(.source.issue.repository.full_name == $repo)
        | select(.source.issue.user.login == $user)
        | .source.issue.number
      '
    )

    if [[ -z "$PR_NUMBERS" ]]; then
      echo "    [INFO] Linked PRs: none"
    else
      echo "    [INFO] Linked PRs: $PR_NUMBERS"
    fi

    # ============================================================
    # PHASE 1: ISSUE HAS NO PR FOR THIS USER
    # ============================================================
    if [[ -z "$PR_NUMBERS" ]]; then
      if (( ASSIGNED_AGE_DAYS >= DAYS )); then
        echo "    [RESULT] Phase 1 → no PR linked + stale (>= $DAYS days)"

        if (( DRY_RUN == 0 )); then
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"
          echo "    [ACTION] Unassigned @$USER from issue #$ISSUE"
        else
          echo "    [DRY RUN] Would unassign @$USER from issue #$ISSUE"
        fi
      else
        echo "    [RESULT] Phase 1 → no PR linked but not stale (< $DAYS days) → KEEP"
      fi

      # No PRs means no Phase 2 work required for this user
      continue
    fi

    # ============================================================
    # PHASE 2: ISSUE HAS PR(s) → check last commit activity
    # ============================================================
    PHASE2_TOOK_ACTION=0

    for PR_NUM in $PR_NUMBERS; do
      # Ensure PR exists in this repo
      if ! PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null); then
        echo "    [SKIP] #$PR_NUM is not a valid PR in $REPO"
        continue
      fi

      echo "    [INFO] PR #$PR_NUM state: $PR_STATE"

      if [[ "$PR_STATE" != "OPEN" ]]; then
        echo "    [SKIP] PR #$PR_NUM is not open"
        continue
      fi

      # Fetch all commits & take the last one (API order + paginate)
      COMMITS=$(gh api "repos/$REPO/pulls/$PR_NUM/commits" --paginate)
      LAST_TS_STR=$(echo "$COMMITS" | jq -r 'last | (.commit.committer.date // .commit.author.date)')
      LAST_TS=$(parse_ts "$LAST_TS_STR")
      PR_AGE_DAYS=$(( (NOW_TS - LAST_TS) / 86400 ))

      echo "    [INFO] PR #$PR_NUM last commit: $LAST_TS_STR (~${PR_AGE_DAYS} days ago)"

      if (( PR_AGE_DAYS >= DAYS )); then
        echo "    [RESULT] Phase 2 → PR #$PR_NUM is stale (>= $DAYS days since last commit)"
        PHASE2_TOOK_ACTION=1

        if (( DRY_RUN == 0 )); then
          gh pr close "$PR_NUM" --repo "$REPO"
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER"
          echo "    [ACTION] Closed PR #$PR_NUM and unassigned @$USER from issue #$ISSUE"
        else
          echo "    [DRY RUN] Would close PR #$PR_NUM and unassign @$USER from issue #$ISSUE"
        fi

        # Per current spec, first stale PR per user/issue is enough
        break
      else
        echo "    [INFO] PR #$PR_NUM is active (< $DAYS days) → KEEP"
      fi
    done

    if (( PHASE2_TOOK_ACTION == 0 )); then
      echo "    [RESULT] Phase 2 → all linked PRs active or not applicable → KEEP"
    fi

  done

  echo
done

echo "------------------------------------------------------------"
echo " Unified Inactivity Bot Complete"
echo " DRY_RUN: $DRY_RUN"
echo "------------------------------------------------------------"
