#!/usr/bin/env bash
set -euo pipefail

DRY_RUN="${DRY_RUN:-true}"

ANCHOR_DATE="2025-12-03"
MEETING_LINK="https://zoom-lfx.platform.linuxfoundation.org/meeting/99912667426?password=5b584a0e-1ed7-49d3-b2fc-dc5ddc888338"
CALENDAR_LINK="https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week"

CANCELLED_DATES=(
  "2025-12-31"
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
    echo "Office Hours cancelled on $TODAY. Exiting."
    exit 0
  fi
done


IS_MEETING_WEEK=$(python3 - <<EOF
from datetime import datetime, date, timezone
d1 = date.fromisoformat("$ANCHOR_DATE")
d2 = datetime.now(timezone.utc).date()
print("true" if (d2 - d1).days % 14 == 0 else "false")
EOF
)

if [ "$IS_MEETING_WEEK" = "false" ]; then
  echo "Not a fortnightly meeting week. Exiting."
  exit 0
fi

if [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "ERROR: GITHUB_REPOSITORY is not set."
  echo "Set it explicitly, e.g.:"
  echo "  export GITHUB_REPOSITORY=owner/repo"
  exit 1
fi

REPO="$GITHUB_REPOSITORY"

PR_DATA=$(gh pr list --repo "$REPO" --state open --json number,author,createdAt)

if [ -z "$PR_DATA" ] || [ "$PR_DATA" = "[]" ]; then
  echo "No open PRs found."
  exit 0
fi

COMMENT_BODY=$(cat <<EOF
Hello, this is the OfficeHourBot.

This is a reminder that the Hiero Python SDK Office Hours are scheduled in approximately 4 hours (14:00 UTC).

This session provides an opportunity to ask questions regarding this Pull Request.

Details:
- Time: 14:00 UTC
- Join Link: [Zoom Meeting]($MEETING_LINK)

Disclaimer: This is an automated reminder. Please verify the schedule [here]($CALENDAR_LINK) for any changes.

From,
The Python SDK Team

EOF
)


echo "$PR_DATA" |
  jq -r '
    sort_by(.author.login)
    | group_by(.author.login)
    | .[]
    | max_by(.createdAt)
    | ((.author.login | endswith("[bot]")) as $is_bot
      | "\(.number) \(.author.login) \($is_bot)")
  ' |
  while read -r PR_NUM AUTHOR IS_BOT; do
    if [[ "$IS_BOT" == "true" ]]; then
      echo "Skipping PR #$PR_NUM because author @$AUTHOR is a bot."
      continue
    fi

    for EXCLUDED in "${EXCLUDED_AUTHORS[@]}"; do
      if [ "$AUTHOR" = "$EXCLUDED" ]; then
        echo "Skipping PR #$PR_NUM by excluded author @$AUTHOR"
        continue 2
      fi
    done

    ALREADY_COMMENTED=$(gh pr view "$PR_NUM" --repo "$REPO" --json comments --jq '.comments[].body' | grep -F "OfficeHourBot" || true)

    if [ -n "$ALREADY_COMMENTED" ]; then
      echo "PR #$PR_NUM already notified. Skipping."
      continue
    fi

    if [ "$DRY_RUN" = "true" ]; then
      echo "----------------------------------------"
      echo "[DRY RUN] Would comment on PR #$PR_NUM"
      echo "[DRY RUN] Author: @$AUTHOR"
      echo "[DRY RUN] Comment body:"
      echo "----------------------------------------"
      echo "$COMMENT_BODY"
      echo "----------------------------------------"
    else
      gh pr comment "$PR_NUM" --repo "$REPO" --body "$COMMENT_BODY"
      echo "Reminder posted to PR #$PR_NUM"
    fi
  done
