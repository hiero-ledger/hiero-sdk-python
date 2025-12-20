#!/usr/bin/env bash
set -euo pipefail

DRY_RUN="${DRY_RUN:-true}"

ANCHOR_DATE="2025-11-12"
MEETING_LINK="https://zoom-lfx.platform.linuxfoundation.org/meeting/92041330205?password=2f345bee-0c14-4dd5-9883-06fbc9c60581"
CALENDAR_LINK="https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week"

CANCELLED_DATES=(
  "2025-12-24"
)

EXCLUDED_AUTHORS=(
  "rbair23"
  "nadineloepfe"
  "exploreriii"
  "manishdait"
  "Dosik13"
  "hendrikebbers"
)

if [ "$DRY_RUN" = "true" ]; then
  echo "=== DRY RUN MODE ENABLED ==="
  echo "No comments will be posted."
fi

TODAY=$(date -u +"%Y-%m-%d")
for CANCELLED in "${CANCELLED_DATES[@]}"; do
  if [ "$TODAY" = "$CANCELLED" ]; then
    echo "Community Call cancelled on $TODAY. Exiting."
    exit 0
  fi
done

IS_MEETING_WEEK=$(python3 - <<EOF
from datetime import date
d1 = date.fromisoformat("$ANCHOR_DATE")
d2 = date.today()
print("true" if (d2 - d1).days % 14 == 0 else "false")
EOF
)

if [ "$IS_MEETING_WEEK" = "false" ]; then
  echo "Not a fortnightly meeting week. Exiting."
  exit 0
fi

if [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "ERROR: GITHUB_REPOSITORY is not set."
  exit 1
fi

REPO="$GITHUB_REPOSITORY"

ISSUE_DATA=$(gh issue list \
  --repo "$REPO" \
  --state open \
  --json number,author,createdAt)

if [ -z "$ISSUE_DATA" ] || [ "$ISSUE_DATA" = "[]" ]; then
  echo "No open issues found."
  exit 0
fi

COMMENT_BODY=$(cat <<EOF
Hello, this is CommunityCallBot.

This is a reminder that the Hiero Python SDK Community Call will begin in approximately 4 hours (14:00 UTC).

The call is an open forum where contributors and users can discuss topics, raise issues, and influence the direction of the Python SDK.

Details:
- Time: 14:00 UTC
- Join Link: [Zoom Meeting]($MEETING_LINK)

Disclaimer: This is an automated reminder. Please verify the schedule [here]($CALENDAR_LINK) for any changes.
EOF
)

echo "$ISSUE_DATA" |
  jq -r '
    group_by(.author.login)
    | .[]
    | sort_by(.createdAt)
    | reverse
    | .[0]
    | "\(.number) \(.author.login)"
  ' |
  while read ISSUE_NUM AUTHOR; do
    for EXCLUDED in "${EXCLUDED_AUTHORS[@]}"; do
      if [ "$AUTHOR" = "$EXCLUDED" ]; then
        echo "Skipping issue #$ISSUE_NUM by excluded author @$AUTHOR"
        continue 2
      fi
    done

    ALREADY_COMMENTED=$(gh issue view "$ISSUE_NUM" \
      --repo "$REPO" \
      --json comments \
      --jq '.comments[].body' | grep -F "CommunityCallBot" || true)

    if [ -n "$ALREADY_COMMENTED" ]; then
      echo "Issue #$ISSUE_NUM already notified. Skipping."
      continue
    fi

    if [ "$DRY_RUN" = "true" ]; then
      echo "----------------------------------------"
      echo "[DRY RUN] Would comment on issue #$ISSUE_NUM"
      echo "[DRY RUN] Author: @$AUTHOR"
      echo "----------------------------------------"
      echo "$COMMENT_BODY"
      echo "----------------------------------------"
    else
      gh issue comment "$ISSUE_NUM" --repo "$REPO" --body "$COMMENT_BODY"
      echo "Reminder posted to issue #$ISSUE_NUM"
    fi
  done
