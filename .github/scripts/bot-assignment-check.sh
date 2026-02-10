#!/bin/bash
set -Eeuo pipefail

# Validate required env vars
if [ -z "${ASSIGNEE:-}" ] || [ -z "${ISSUE_NUMBER:-}" ] || [ -z "${REPO:-}" ]; then
  echo "Error: Missing required environment variables (ASSIGNEE, ISSUE_NUMBER, REPO)."
  exit 1
fi

echo "Checking assignment rules for user $ASSIGNEE on issue #$ISSUE_NUMBER"

# Helper functions
get_permission() {
  gh api "repos/${REPO}/collaborators/${ASSIGNEE}/permission" --jq '.permission' 2>/dev/null || echo "none"

}

is_spam_user() {
  local spam_file=".github/spam-list.txt"
  
  # Check static spam list
  if [[ -f "$spam_file" ]]; then
    if grep -vE '^\s*#|^\s*$' "$spam_file" | grep -qxF "$ASSIGNEE"; then
      return 0
    fi
  else
    echo "Spam list file not found.  Treating as empty." >&2
  fi
  return 1
}

issue_has_gfi() {
  local has
  has=$(gh api "repos/${REPO}/issues/${ISSUE_NUMBER}" --jq 'any(.labels[]; .name=="Good First Issue")' || echo "false")
  [[ "$has" == "true" ]]
}

assignments_count() {
  # Count only issues (not PRs) assigned to the user, using structured isPullRequest field
  gh issue list --repo "${REPO}" --assignee "${ASSIGNEE}" --state open --limit 100 --json number,isPullRequest --jq '[.[] | select(.isPullRequest | not)] | length'
}

remove_assignee() {
  gh issue edit "${ISSUE_NUMBER}" --repo "${REPO}" --remove-assignee "${ASSIGNEE}"
}

post_comment() {
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$1"
}

msg_spam_non_gfi() {
  cat <<EOF
Hi @$ASSIGNEE, this is the Assignment Bot. 

:warning: **Assignment Restricted**

Your account currently has limited assignment privileges. You may only be assigned to issues labeled **Good First Issue**. 

**Current Restrictions:**
- :white_check_mark: Can be assigned to 'Good First Issue' labeled issues (maximum 1 at a time)
- :x: Cannot be assigned to other issues

**How to have restrictions lifted:**
1. Successfully complete and merge your assigned Good First Issue
2. Demonstrate consistent, quality contributions
3. Contact a maintainer to review your restriction status

Thank you for your understanding!
EOF
}

msg_spam_limit_exceeded() {
  local count="$1"
  cat <<EOF
Hi @$ASSIGNEE, this is the Assignment Bot.

:warning: **Assignment Limit Exceeded**

Your account currently has limited assignment privileges with a maximum of **1 open issue assignment** at a time.

You currently have $count open issue(s) assigned.  Please complete and merge your existing assignment before requesting a new one.

**Current Restrictions:**
- Maximum 1 open issue assignment at a time
- Can only be assigned to 'Good First Issue' labeled issues

**How to have restrictions lifted:**
1. Successfully complete and merge your current assigned issue
2. Demonstrate consistent, quality contributions
3. Contact a maintainer to review your restriction status

Thank you for your cooperation!
EOF
}

msg_normal_limit_exceeded() {
  cat <<EOF
Hi @$ASSIGNEE, this is the Assignment Bot.

Assigning you to this issue would exceed the limit of 2 open issue assignments.

Please resolve and merge your existing assigned issues before requesting new ones.
EOF
}

# Check permission level
PERMISSION="$(get_permission)"
echo "User permission level: $PERMISSION"

if [[ "$PERMISSION" == "admin" || "$PERMISSION" == "write" ]]; then
  echo "User is a maintainer or committer.  Limit does not apply."
  exit 0
fi

# Check spam status
SPAM=false
if is_spam_user; then
  SPAM=true
  echo "User is in spam list.  Applying restricted assignment rules."
fi

COUNT="$(assignments_count)"

# Apply assignment rules
if [[ "$SPAM" == "true" ]]; then
  # Spam users can only be assigned to Good First Issues
  if ! issue_has_gfi; then
    echo "Issue does not have 'Good First Issue' label."
    echo "Spam-listed user attempting to assign non-GFI issue.  Revoking assignment."
    remove_assignee
    post_comment "$(msg_spam_non_gfi)"
    exit 1
  fi
  
  echo "Issue has 'Good First Issue' label."
  
  # Spam users have a limit of 1 open assignment
  echo "Spam-listed user has $COUNT open assignments."
  
  if (( COUNT > 1 )); then
    echo "Spam user limit exceeded (Max 1 allowed). Revoking assignment."
    remove_assignee
    post_comment "$(msg_spam_limit_exceeded "$COUNT")"
    exit 1
  fi
  
  echo "Spam-listed user assignment valid. User has $COUNT assignment(s)."
else
  # Normal users have a limit of 2 open assignments
  echo "Current open assignments count: $COUNT"
  
  if (( COUNT > 2 )); then
    echo "Limit exceeded (Max 2 allowed). Revoking assignment."
    remove_assignee
    post_comment "$(msg_normal_limit_exceeded)"
    exit 1
  fi
  
  echo "Assignment valid. User has $COUNT assignments."
fi
