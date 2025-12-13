#!/bin/bash

# Community Call Reminder Bot Script
# This script checks if it's a meeting week and posts reminders to open issues

set -e

# Configuration - Consider moving to repository variables for easier maintenance
# Anchor date: Date of the first Hiero Python SDK Community Call (Wednesday, December 11, 2025)
# This date is used as the reference point for fortnightly meeting calculations
ANCHOR_DATE="${ANCHOR_DATE:-2025-12-11}"  # Fixed to be a Wednesday
MEETING_LINK="${MEETING_LINK:-https://zoom-lfx.platform.linuxfoundation.org/meeting/92041330205?password=2f345bee-0c14-4dd5-9883-06fbc9c60581}"
CALENDAR_LINK="${CALENDAR_LINK:-https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week}"
DRY_RUN="${DRY_RUN:-false}"
REPO="${REPO:-$1}"

if [ -z "$REPO" ]; then
  echo "Error: Repository not specified. Usage: $0 <repo> or set REPO environment variable"
  exit 1
fi

echo "=== Community Call Reminder Bot ==="
echo "Repository: $REPO"
echo "Anchor Date: $ANCHOR_DATE"
echo "Dry Run: $DRY_RUN"
echo "=================================="

# Check if it's a meeting week
IS_MEETING_WEEK=$(python3 -c "
from datetime import date
import os
d1 = date.fromisoformat('$ANCHOR_DATE')
d2 = date.today()
days_diff = (d2 - d1).days
print('true' if days_diff >= 0 and days_diff % 14 == 0 else 'false')
")

if [ "$IS_MEETING_WEEK" = "false" ]; then
  echo "Not a fortnightly meeting week. Skipping execution."
  exit 0
fi

echo "Meeting week detected. Proceeding to check open issues."

# Get all open issues with author information and find latest issue per user
# This approach avoids bash associative arrays for better portability
LATEST_ISSUES=$(gh issue list --repo "$REPO" --state open --json number,author --jq '
  group_by(.author.login) | 
  map({
    author: .[0].author.login, 
    latest_issue: (map(.number) | max)
  }) | 
  .[] | 
  "\(.latest_issue):\(.author)"
')

if [ -z "$LATEST_ISSUES" ]; then
  echo "No open issues found."
  exit 0
fi

# Prepare comment body
COMMENT_BODY=$(cat <<EOF
Hello, this is the Community Call Bot.

This is a reminder that the Hiero Python SDK Community Call is scheduled in approximately 4 hours (14:00 UTC).

We host fortnightly community calls where we want to hear from the community about all things related to the Python SDK. This is a great opportunity to discuss this issue, ask questions, or provide feedback directly to the maintainers and community.

Details:
- Time: 14:00 UTC (2:00 PM UTC)
- Join Link: [Zoom Meeting]($MEETING_LINK)

Disclaimer: This is an automated reminder. Please subscribe to the meeting to be notified of any changes and check the Hiero calendar [here]($CALENDAR_LINK).
EOF
)

# Process only the latest issue per user
echo "$LATEST_ISSUES" | while IFS=':' read -r issue_num author; do
  echo "Processing Issue #$issue_num (latest for user: $author)"
  
  # Check for bot's unique signature to prevent duplicate comments
  ALREADY_COMMENTED=$(gh issue view "$issue_num" --repo "$REPO" --json comments --jq '.comments[].body' | grep -F "Hello, this is the Community Call Bot." || true)

  if [ -z "$ALREADY_COMMENTED" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "DRY RUN: Would post reminder to Issue #$issue_num"
      echo "Comment body:"
      echo "$COMMENT_BODY"
      echo "---"
    else
      gh issue comment "$issue_num" --repo "$REPO" --body "$COMMENT_BODY"
      echo "Reminder posted to Issue #$issue_num"
    fi
  else
    echo "Issue #$issue_num already notified. Skipping."
  fi
done

echo "Community call reminder process completed."