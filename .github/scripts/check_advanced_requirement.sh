#!/bin/bash

# 1. Check for Exemptions (Triage, Committers, Maintainers)
# Using 'triage', 'write', or 'admin' covers all core teams.
PERM_JSON=$(gh api repos/$REPO/collaborators/$ASSIGNEE/permission)
PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission')

if [[ "$PERMISSION" == "admin" ]] || [[ "$PERMISSION" == "write" ]] || [[ "$PERMISSION" == "triage" ]]; then
  echo "User @$ASSIGNEE is a core member ($PERMISSION). Qualification check skipped."
  exit 0
fi

# 2. Get counts of completed issues
# IMPROVEMENT: We exclude issues closed as 'not planned' (won't fix/duplicate)
# This ensures we only count issues that were actually "solved".
BASE_QUERY="repo:$REPO is:issue is:closed assignee:$ASSIGNEE -reason:\"not planned\""

GFI_COUNT=$(gh api "search/issues?q=$BASE_QUERY+label:\"good first issue\"" --jq '.total_count')
INT_COUNT=$(gh api "search/issues?q=$BASE_QUERY+label:\"intermediate\"" --jq '.total_count')

echo "Stats for @$ASSIGNEE: GFI: $GFI_COUNT, Intermediate: $INT_COUNT"

# 3. Validation Logic
if (( GFI_COUNT >= 1 )) && (( INT_COUNT >= 1 )); then
  echo "Qualification met."
  exit 0
else
  echo "Qualification failed. Revoking assignment."

  # Remove the assignee
  gh issue edit $ISSUE_NUMBER --repo $REPO --remove-assignee "$ASSIGNEE"

  # 4. Message Improvement: Mentioning WHY advanced exists (Risk & Testing)
  MSG="Hi @$ASSIGNEE, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase. They require significant testing and can impact automation and CI behavior. Because of this, we require developers to demonstrate familiarity with the repo first.

**Requirement:**
- Complete at least **1** 'good first issue' (You have: **$GFI_COUNT**)
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please feel free to pick up an [intermediate issue](https://github.com/$REPO/labels/intermediate) to get started! We look forward to your contributions."

  gh issue comment $ISSUE_NUMBER --repo $REPO --body "$(printf "$MSG")"
  
  exit 1
fi