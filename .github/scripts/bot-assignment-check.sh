#!/bin/bash

if [ -z "$ASSIGNEE" ] || [ -z "$ISSUE_NUMBER" ] || [ -z "$REPO" ]; then
  echo "Error: Missing required environment variables (ASSIGNEE, ISSUE_NUMBER, REPO)."
  exit 1
fi

echo "Checking assignment rules for user $ASSIGNEE on issue #$ISSUE_NUMBER"

PERM_JSON=$(gh api repos/$REPO/collaborators/$ASSIGNEE/permission)
PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission')

echo "User permission level: $PERMISSION"

if [[ "$PERMISSION" == "admin" ]] || [[ "$PERMISSION" == "write" ]]; then
  echo "User is a maintainer or committer. Limit does not apply."
  exit 0
fi

ASSIGNMENTS_JSON=$(gh issue list --repo $REPO --assignee "$ASSIGNEE" --state open --json number)
COUNT=$(echo "$ASSIGNMENTS_JSON" | jq '. | length')

echo "Current open assignments count: $COUNT"

if (( COUNT > 2 )); then
  echo "Limit exceeded (Max 2 allowed). Revoking assignment."

  gh issue edit $ISSUE_NUMBER --repo $REPO --remove-assignee "$ASSIGNEE"

  MSG="Hi @$ASSIGNEE, this is the Assignment Bot."
  MSG="$MSG\n\nAssigning you to this issue would exceed the limit of 2 open assignments."
  MSG="$MSG\n\nPlease resolve and merge your existing assigned issues before requesting new ones."

  gh issue comment $ISSUE_NUMBER --repo $REPO --body "$(printf "$MSG")"
  
  exit 1
else
  echo "Assignment valid. User has $COUNT assignments."
fi