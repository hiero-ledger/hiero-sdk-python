#!/bin/bash
set -euo pipefail

# 1. Check for Exemptions (Triage, Committers, Maintainers)
# Handle non-collaborator (404) and quote variables
PERM_JSON=$(gh api "repos/$REPO/collaborators/$ASSIGNEE/permission" 2>/dev/null || echo '{"permission":"none"}')
PERMISSION=$(echo "$PERM_JSON" | jq -r '.permission // "none"')

if [[ "$PERMISSION" =~ ^(admin|write|triage)$ ]]; then
  echo "User @$ASSIGNEE is a core member ($PERMISSION). Qualification check skipped."
  exit 0
fi

# 2. Get counts of completed issues
#  Use -f q= to handle URL encoding for labels with spaces automatically
GFI_QUERY="repo:$REPO is:issue is:closed assignee:$ASSIGNEE -reason:\"not planned\" label:\"good first issue\""
INT_QUERY="repo:$REPO is:issue is:closed assignee:$ASSIGNEE -reason:\"not planned\" label:\"intermediate\""

GFI_COUNT=$(gh api "search/issues" -f q="$GFI_QUERY" --jq '.total_count')
INT_COUNT=$(gh api "search/issues" -f q="$INT_QUERY" --jq '.total_count')

# Ensure counts are numeric (default to 0)
GFI_COUNT=${GFI_COUNT:-0}
INT_COUNT=${INT_COUNT:-0}

echo "Stats for @$ASSIGNEE: GFI: $GFI_COUNT, Intermediate: $INT_COUNT"

# 3. Validation Logic
if (( GFI_COUNT >= 1 )) && (( INT_COUNT >= 1 )); then
  echo "Qualification met."
  exit 0
else
  echo "Qualification failed. Revoking assignment."

  # Quote variables to prevent word-splitting
  gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --remove-assignee "$ASSIGNEE"

  # 4. Message
  MSG="Hi @$ASSIGNEE, I cannot assign you to this issue yet.

**Why?**
Advanced issues involve high-risk changes to the core codebase. They require significant testing and can impact automation and CI behavior. Because of this, we require developers to demonstrate familiarity with the repo first.

**Requirement:**
- Complete at least **1** 'good first issue' (You have: **$GFI_COUNT**)
- Complete at least **1** 'intermediate' issue (You have: **$INT_COUNT**)

Please feel free to pick up an [intermediate issue](https://github.com/hiero-ledger/hiero-sdk-python/labels/intermediate) to get started! We look forward to your contributions."

  #  Use the variable safely without printf format vulnerabilities
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$MSG"
  
  exit 1
fi