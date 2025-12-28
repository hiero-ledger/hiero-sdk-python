#!/usr/bin/env bash
set -euo pipefail

# Unified Inactivity Bot (Phase 1 + Phase 2)
# DRY_RUN controls behaviour:
#   DRY_RUN = 1 -> simulate only (no changes, just logs)
#   DRY_RUN = 0 -> real actions (comments, closes, unassigns)

REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DAYS="${DAYS:-21}"
DRY_RUN="${DRY_RUN:-0}"

# Normalise DRY_RUN input ("true"/"false" -> 1/0, case-insensitive)
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
echo " Unified Inactivity Bot"
echo " Repo:     $REPO"
echo " Threshold $DAYS days"
echo " DRY_RUN:  $DRY_RUN"
echo "------------------------------------------------------------"

# current time (epoch seconds)
NOW_TS=$(date +%s)

# Convert GitHub ISO timestamp -> epoch seconds (works on Linux/BSD)
parse_ts() {
  local ts="$1"
  if date --version >/dev/null 2>&1; then
    date -d "$ts" +%s
  else
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +"%s"
  fi
}

# Quick gh availability/auth checks
if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found. Install it and ensure it's on PATH."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "WARN: gh auth status failed — ensure gh is logged in for non-dry runs."
fi

# Get list of open issues with assignees (pagination via gh)
ISSUES=$(
  gh api "repos/$REPO/issues" --paginate --jq '.[] 
    | select(.state=="open" and (.assignees|length>0) and (.pull_request|not))
    | .number' 2>/dev/null || true
)

for ISSUE in $ISSUES; do
  echo "============================================================"
  echo " ISSUE #$ISSUE"
  echo "============================================================"

  ISSUE_JSON=$(gh api "repos/$REPO/issues/$ISSUE" 2>/dev/null || echo "{}")
  ISSUE_CREATED_AT=$(echo "$ISSUE_JSON" | jq -r '.created_at // empty')
  ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[]?.login' 2>/dev/null || true)

  echo "  [INFO] Issue created at: ${ISSUE_CREATED_AT:-(unknown)}"
  echo

  # Fetch full timeline with pagination and flatten array 
  TIMELINE=$(gh api --paginate -H "Accept: application/vnd.github.mockingbird-preview+json" "repos/$REPO/issues/$ISSUE/timeline" 2>/dev/null | jq -s 'add' || echo "[]")
  TIMELINE=${TIMELINE:-'[]'}

  if [[ -z "${ASSIGNEES// }" ]]; then
    echo "  [INFO] No assignees for this issue, skipping."
    echo
    continue
  fi

  for USER in $ASSIGNEES; do
    echo "  → Checking assignee: $USER"

    # Determine assignment timestamp
    ASSIGN_EVENT_JSON=$(jq -c --arg user "$USER" '
      [ .[] | select(.event == "assigned") | select(.assignee.login == $user) ] | last // empty' <<<"$TIMELINE" 2>/dev/null || echo "")

    if [[ -n "$ASSIGN_EVENT_JSON" && "$ASSIGN_EVENT_JSON" != "null" ]]; then
      ASSIGNED_AT=$(echo "$ASSIGN_EVENT_JSON" | jq -r '.created_at // empty')
      ASSIGN_SOURCE="assignment_event"
    else
      # FIX: Do not fallback to issue creation date
      ASSIGNED_AT=""
      ASSIGN_SOURCE="not_found"
    fi

    if [[ -n "$ASSIGNED_AT" ]]; then
      ASSIGNED_TS=$(parse_ts "$ASSIGNED_AT")
      ASSIGNED_AGE_DAYS=$(( (NOW_TS - ASSIGNED_TS) / 86400 ))
    else
      # Safety valve: if assignment event is missing, skip checking to prevent false positives
      echo "    [WARN] Could not find 'assigned' event in timeline. Skipping inactivity check for safety."
      continue
    fi

    echo "    [INFO] Assignment source: $ASSIGN_SOURCE"
    echo "    [INFO] Assigned at:      ${ASSIGNED_AT:-(unknown)} (~${ASSIGNED_AGE_DAYS} days ago)"

    # Determine PRs cross-referenced from the same repo
    PR_NUMBERS=$(jq -r --arg repo "$REPO" '
      .[] |
      select(.event == "cross-referenced") |
      select(.source.issue.pull_request != null) |
      select(.source.issue.repository.full_name == $repo) |
      .source.issue.number' <<<"$TIMELINE" 2>/dev/null || true)

    PR_NUMBERS=$(echo "$PR_NUMBERS" | sed '/^[[:space:]]*$/d' || true)

    # PHASE 1: no PRs attached
    if [[ -z "${PR_NUMBERS// }" ]]; then
      echo "    [INFO] Linked PRs: none"

      if (( ASSIGNED_AGE_DAYS >= DAYS )); then
        echo "    [RESULT] Phase 1 -> stale assignment (>= $DAYS days, no PR)"

        if (( DRY_RUN == 0 )); then
          MESSAGE=$(cat <<EOF
Hi @$USER, this is InactivityBot 👋

You were assigned to this issue **${ASSIGNED_AGE_DAYS} days** ago, and there is currently no open pull request linked to it.
To keep the backlog available for active contributors, I'm unassigning you for now.

If you'd like to continue working on this later, feel free to get re-assigned or comment here and we'll gladly assign it back to you. 🙂
EOF
)
          gh issue comment "$ISSUE" --repo "$REPO" --body "$MESSAGE" || echo "WARN: couldn't post comment (gh error)"
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER" || echo "WARN: couldn't remove assignee (gh error)"
          echo "    [ACTION] Commented and unassigned @$USER from issue #$ISSUE"
        else
          echo "    [DRY RUN] Would comment + unassign @$USER from issue #$ISSUE (Phase 1 stale)"
        fi
      else
        echo "    [RESULT] Phase 1 -> no PR linked but not stale (< $DAYS days) -> KEEP"
      fi

      echo
      continue
    fi

    # PHASE 2: process linked PR(s)
    echo "    [INFO] Linked PRs: $PR_NUMBERS"
    PHASE2_TOUCHED=0

    for PR_NUM in $PR_NUMBERS; do
      if ! PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null); then
        echo "    [SKIP] #$PR_NUM is not a valid PR in $REPO"
        continue
      fi

      echo "    [INFO] PR #$PR_NUM state: $PR_STATE"
      if [[ "$PR_STATE" != "OPEN" ]]; then
        echo "    [SKIP] PR #$PR_NUM is not open"
        continue
      fi

      COMMITS_JSON=$(gh api "repos/$REPO/pulls/$PR_NUM/commits" --paginate 2>/dev/null || echo "[]")
      LAST_TS_STR=$(jq -r 'last? | (.commit.committer.date // .commit.author.date) // empty' <<<"$COMMITS_JSON" 2>/dev/null || echo "")
      if [[ -n "$LAST_TS_STR" ]]; then
        LAST_TS=$(parse_ts "$LAST_TS_STR")
        PR_AGE_DAYS=$(( (NOW_TS - LAST_TS) / 86400 ))
      else
        PR_AGE_DAYS=$((DAYS+1))
      fi

      echo "    [INFO] PR #$PR_NUM last commit: ${LAST_TS_STR:-(unknown)} (~${PR_AGE_DAYS} days ago)"

      if (( PR_AGE_DAYS >= DAYS )); then
        PHASE2_TOUCHED=1
        echo "    [RESULT] Phase 2 -> PR #$PR_NUM is stale (>= $DAYS days since last commit)"

        if (( DRY_RUN == 0 )); then
          MESSAGE=$(cat <<EOF
Hi @$USER, this is InactivityBot 👋

This pull request has had no new commits for **${PR_AGE_DAYS} days**, so I'm closing it and unassigning you from the linked issue to keep the backlog healthy.

You're very welcome to open a new PR or ask to be re-assigned when you're ready to continue working on this. 🚀
EOF
)
          gh pr comment "$PR_NUM" --repo "$REPO" --body "$MESSAGE" || echo "WARN: couldn't comment on PR"
          gh pr close "$PR_NUM" --repo "$REPO" || echo "WARN: couldn't close PR"
          gh issue edit "$ISSUE" --repo "$REPO" --remove-assignee "$USER" || echo "WARN: couldn't remove assignee"
          echo "    [ACTION] Commented on PR #$PR_NUM, closed it, and unassigned @$USER from issue #$ISSUE"
        else
          echo "    [DRY RUN] Would comment, close PR #$PR_NUM, and unassign @$USER from issue #$ISSUE"
        fi
      else
        echo "    [INFO] PR #$PR_NUM is active (< $DAYS days) -> KEEP"
      fi
    done

    if (( PHASE2_TOUCHED == 0 )); then
      echo "    [RESULT] Phase 2 -> all linked PRs active or not applicable -> KEEP"
    fi

    echo
  done
done

echo "------------------------------------------------------------"
echo " Unified Inactivity Bot Complete"
echo " DRY_RUN: $DRY_RUN"
echo "------------------------------------------------------------"