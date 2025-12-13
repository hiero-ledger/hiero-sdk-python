#!/bin/bash

# Mentor Assignment Script for New Contributors
# This script automatically assigns a mentor from the triage team to new contributors
# working on "good first issue" labeled issues.

if [ -z "$ASSIGNEE" ] || [ -z "$ISSUE_NUMBER" ] || [ -z "$REPO" ]; then
  echo "Error: Missing required environment variables (ASSIGNEE, ISSUE_NUMBER, REPO)."
  exit 1
fi

echo "Processing mentor assignment for user $ASSIGNEE on issue #$ISSUE_NUMBER"

# Check if the issue has "good first issue" label
LABELS_JSON=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json labels)
HAS_GFI_LABEL=$(echo "$LABELS_JSON" | jq -r '.labels[] | select(.name == "good first issue") | .name')

if [ -z "$HAS_GFI_LABEL" ]; then
  echo "Issue #$ISSUE_NUMBER does not have 'good first issue' label. Skipping mentor assignment."
  exit 0
fi

echo "Issue has 'good first issue' label. Checking if $ASSIGNEE is a new contributor..."

# Check if user is a maintainer/committer (they don't need a mentor)
PERM_JSON=$(gh api "repos/$REPO/collaborators/$ASSIGNEE/permission" 2>/dev/null || echo '{"permission":"none"}')
PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission')

echo "User permission level: $PERMISSION"

if [[ "$PERMISSION" == "admin" ]] || [[ "$PERMISSION" == "write" ]]; then
  echo "User is a maintainer or committer. No mentor needed."
  exit 0
fi

# Check if user has any merged PRs (indicating they're not a new contributor)
MERGED_PRS=$(gh pr list --repo "$REPO" --author "$ASSIGNEE" --state merged --limit 1 --json number | jq '. | length')

if [ "$MERGED_PRS" -gt 0 ]; then
  echo "User $ASSIGNEE has previously merged PRs. Not a new contributor, skipping mentor assignment."
  exit 0
fi

echo "User $ASSIGNEE is a new contributor. Assigning a mentor..."

# Get list of triage team members
# Note: GitHub API for team members requires org-level permissions
# Using a fallback list of known mentors as a backup
TRIAGE_TEAM="hiero-ledger/hiero-sdk-python-triage"

# Try to get team members via API (requires appropriate permissions)
MENTORS_JSON=$(gh api "orgs/hiero-ledger/teams/hiero-sdk-python-triage/members" 2>/dev/null || echo "[]")
MENTORS_COUNT=$(echo "$MENTORS_JSON" | jq '. | length')

if [ "$MENTORS_COUNT" -eq 0 ]; then
  echo "Could not fetch team members. Using team mention instead."
  MENTOR="@$TRIAGE_TEAM"
  MENTOR_MENTION="$TRIAGE_TEAM"
else
  # Select a random mentor from the list (excluding the assignee)
  AVAILABLE_MENTORS=$(echo "$MENTORS_JSON" | jq -r --arg assignee "$ASSIGNEE" '[.[] | select(.login != $assignee) | .login] | @json')
  AVAILABLE_COUNT=$(echo "$AVAILABLE_MENTORS" | jq '. | length')
  
  if [ "$AVAILABLE_COUNT" -eq 0 ]; then
    echo "No available mentors found."
    MENTOR="@$TRIAGE_TEAM"
    MENTOR_MENTION="$TRIAGE_TEAM"
  else
    # Select random mentor
    RANDOM_INDEX=$((RANDOM % AVAILABLE_COUNT))
    MENTOR=$(echo "$AVAILABLE_MENTORS" | jq -r ".[$RANDOM_INDEX]")
    MENTOR_MENTION="@$MENTOR"
    echo "Selected mentor: $MENTOR"
  fi
fi

# Post welcome message with mentor assignment
WELCOME_MSG=$(cat <<EOF
👋 **Welcome to the Hiero Python SDK, @$ASSIGNEE!**

We're excited to have you contribute to our project! You are now officially assigned to this issue.

📚 **Before you begin, please:**
1. Read the issue description carefully
2. Check out our [Contributing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/CONTRIBUTING.md)
3. Review the [DCO signing guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/signing.md)

🧑‍🏫 **Your Mentor:** $MENTOR_MENTION

We've assigned a mentor from our triage team to help guide you through your first contribution. Feel free to reach out to them by mentioning them in the comments if you have any questions or need assistance.

💡 **Helpful Resources:**
- [Changelog Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/changelog_entry.md)
- [Testing Guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/testing.md)
- [Discord Community](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)

⭐ If you enjoy working on this project, don't forget to [star the repository](https://github.com/hiero-ledger/hiero-sdk-python)!

Best of luck with your contribution!
*From the Hiero Python SDK Team* 🚀
EOF
)

# Check if we've already posted a welcome message for this user on this issue
EXISTING_WELCOME=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --comments --json comments -q ".comments[] | select(.body | contains(\"Welcome to the Hiero Python SDK, @$ASSIGNEE\")) | .id" | head -1)

if [ -n "$EXISTING_WELCOME" ]; then
  echo "Welcome message already posted for $ASSIGNEE on issue #$ISSUE_NUMBER. Skipping."
  exit 0
fi

echo "Posting welcome message..."
gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$WELCOME_MSG"

echo "Mentor assignment complete!"
