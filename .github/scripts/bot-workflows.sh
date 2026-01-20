#!/usr/bin/env bash
set -euo pipefail

# Workflow Failure Notifier - Looks up PR and posts failure notification
# DRY_RUN controls behaviour:
#   DRY_RUN = 1 -> simulate only (no changes, just logs)
#   DRY_RUN = 0 -> real actions (post PR comments)

# Validate required environment variables
FAILED_WORKFLOW_NAME="${FAILED_WORKFLOW_NAME:-}"
FAILED_RUN_ID="${FAILED_RUN_ID:-}"
GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
REPO="${REPO:-${GITHUB_REPOSITORY:-}}"
DRY_RUN="${DRY_RUN:-1}"
PR_NUMBER="${PR_NUMBER:-}"

export GH_TOKEN

# Normalise DRY_RUN input ("true"/"false" -> 1/0, case-insensitive)
shopt -s nocasematch
case "$DRY_RUN" in
  1|0) ;;
  "true")  DRY_RUN=1 ;;
  "false") DRY_RUN=0 ;;
  *)
    echo "ERROR: DRY_RUN must be one of: true, false, 1, 0 (got: $DRY_RUN)"
    exit 1
    ;;
esac
shopt -u nocasematch

# Validate required variables or set defaults in dry-run mode
if [[ -z "$FAILED_WORKFLOW_NAME" ]]; then
  if (( DRY_RUN == 1 )); then
    echo "WARN: FAILED_WORKFLOW_NAME not set, using default for dry-run."
    FAILED_WORKFLOW_NAME="DRY_RUN_TEST"
  else
    echo "ERROR: FAILED_WORKFLOW_NAME environment variable not set."
    exit 1
  fi
fi

if [[ -z "$FAILED_RUN_ID" ]]; then
  if (( DRY_RUN == 1 )); then
    echo "WARN: FAILED_RUN_ID not set, using default for dry-run."
    FAILED_RUN_ID="12345"
  else
    echo "ERROR: FAILED_RUN_ID environment variable not set."
    exit 1
  fi
fi

# Validate FAILED_RUN_ID is numeric (always check when provided)
if ! [[ "$FAILED_RUN_ID" =~ ^[0-9]+$ ]]; then
  echo "ERROR: FAILED_RUN_ID must be a numeric integer (got: '$FAILED_RUN_ID')"
  exit 1
fi

if [[ -z "$GH_TOKEN" ]]; then
  if (( DRY_RUN == 1 )); then
    echo "WARN: GH_TOKEN not set. Some dry-run operations may fail."
  else
    echo "ERROR: GH_TOKEN (or GITHUB_TOKEN) environment variable not set."
    exit 1
  fi
fi

if [[ -z "$REPO" ]]; then
  echo "ERROR: REPO environment variable not set."
  exit 1
fi

echo "------------------------------------------------------------"
echo " Workflow Failure Notifier"
echo " Repo:                $REPO"
echo " Failed Workflow:     $FAILED_WORKFLOW_NAME"
echo " Failed Run ID:       $FAILED_RUN_ID"
echo " DRY_RUN:             $DRY_RUN"
echo "------------------------------------------------------------"

# Quick gh availability/auth checks
if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found. Install it and ensure it's on PATH."
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq not found. Install it and ensure it's on PATH."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  if (( DRY_RUN == 0 )); then
    echo "ERROR: gh authentication required for non-dry-run mode."
    exit 1
  else
    echo "WARN: gh auth status failed — some dry-run operations may not work."
  fi
fi

# PR lookup logic - use PR_NUMBER from workflow_run payload if available, otherwise fallback to branch-based approach
echo "Looking up PR for failed workflow run..."

# Use PR_NUMBER from workflow_run payload if provided (optimized path)
if [[ -n "$PR_NUMBER" ]]; then
  echo "Using PR number from workflow_run payload: $PR_NUMBER"
else
  echo "PR_NUMBER not provided, falling back to branch-based lookup..."

  HEAD_BRANCH=$(gh run view "$FAILED_RUN_ID" --repo "$REPO" --json headBranch --jq '.headBranch' 2>/dev/null || echo "")

  if [[ -z "$HEAD_BRANCH" ]]; then
    if (( DRY_RUN == 1 )); then
      echo "WARN: Could not retrieve head branch in dry-run mode (run ID may be invalid). Exiting gracefully."
      exit 0
    else
      echo "ERROR: Could not retrieve head branch from workflow run $FAILED_RUN_ID"
      exit 1
    fi
  fi

  echo "Found head branch: $HEAD_BRANCH"

  # Find PR number for this branch (only open PRs)
  PR_NUMBER=$(gh pr list --repo "$REPO" --head "$HEAD_BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo "")

  if [[ -z "$PR_NUMBER" ]]; then
    if (( DRY_RUN == 1 )); then
      echo "No PR associated with workflow run $FAILED_RUN_ID, but DRY_RUN=1 - exiting successfully."
      exit 0
    else
      echo "INFO: No open PR found for branch '$HEAD_BRANCH' (workflow run $FAILED_RUN_ID). Nothing to notify."
      exit 0
    fi
  fi
fi

echo "Found PR #$PR_NUMBER"

# Build notification message with failure details and documentation links
MARKER="<!-- workflowbot:workflow-failure-notifier -->"
COMMENT=$(cat <<EOF
$MARKER
Hi, this is WorkflowBot. 
Your pull request cannot be merged as it is not passing all our workflow checks. 
Please click on each check to review the logs and resolve issues so all checks pass.
To help you:
- [DCO signing guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/signing.md)
- [Changelog guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/changelog_entry.md)
- [Merge conflicts guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/merge_conflicts.md)
- [Rebase guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/rebasing.md)
- [Testing guide](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/testing.md)
- [Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)
- [Community Calls](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)
Thank you for contributing!
From the Hiero Python SDK Team
EOF
)

# Check for duplicate comments using the correct endpoint for issue comments
PAGE=1
DUPLICATE_EXISTS="false"
MAX_PAGES=10  # Safety bound

while (( PAGE <= MAX_PAGES )); do
  COMMENTS_PAGE=$(gh api \
    --header 'Accept: application/vnd.github.v3+json' \
    "/repos/$REPO/issues/$PR_NUMBER/comments?per_page=100&page=$PAGE" 2>/dev/null || echo "[]")
  
  # Check if the page is empty (no more comments)
  if [[ $(echo "$COMMENTS_PAGE" | jq 'length') -eq 0 ]]; then
    break
  fi

  # Check this page for the marker instead of concatenating invalid JSON
  if echo "$COMMENTS_PAGE" | jq -e --arg marker "$MARKER" '.[] | select(.body | contains($marker))' >/dev/null 2>&1; then
    DUPLICATE_EXISTS="true"
    echo "Found existing duplicate comment. Skipping."
    break
  fi

  PAGE=$((PAGE + 1))
done

if [[ "$DUPLICATE_EXISTS" == "false" ]]; then
  echo "No existing duplicate comment found."
fi

# Dry-run mode or actual posting
if (( DRY_RUN == 1 )); then
  echo "[DRY RUN] Would post comment to PR #$PR_NUMBER:"
  echo "----------------------------------------"
  echo "$COMMENT"
  echo "----------------------------------------"
  if [[ "$DUPLICATE_EXISTS" == "true" ]]; then
    echo "[DRY RUN] Would skip posting due to duplicate comment"
  else
    echo "[DRY RUN] Would post new comment (no duplicates found)"
  fi
else
  if [[ "$DUPLICATE_EXISTS" == "true" ]]; then
    echo "Comment already exists, skipping."
  else
    echo "Posting new comment to PR #$PR_NUMBER..."
    if gh pr comment "$PR_NUMBER" --repo "$REPO" --body "$COMMENT"; then
      echo "Successfully posted comment to PR #$PR_NUMBER"
    else
      echo "ERROR: Failed to post comment to PR #$PR_NUMBER"
      exit 1
    fi
  fi
fi

echo "------------------------------------------------------------"
echo " Workflow Failure Notifier Complete"
echo " DRY_RUN: $DRY_RUN"
echo "------------------------------------------------------------"
