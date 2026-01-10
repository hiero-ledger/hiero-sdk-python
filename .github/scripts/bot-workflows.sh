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
DRY_RUN="${DRY_RUN:-0}"

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

# Exit with error if required variables missing
if [[ -z "$FAILED_WORKFLOW_NAME" ]]; then
  echo "ERROR: FAILED_WORKFLOW_NAME environment variable not set."
  exit 1
fi

if [[ -z "$FAILED_RUN_ID" ]]; then
  echo "ERROR: FAILED_RUN_ID environment variable not set."
  exit 1
fi

if [[ -z "$GH_TOKEN" ]]; then
  echo "ERROR: GH_TOKEN (or GITHUB_TOKEN) environment variable not set."
  exit 1
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

if ! gh auth status >/dev/null 2>&1; then
  echo "WARN: gh auth status failed — ensure gh is logged in for non-dry runs."
fi

# PR lookup logic - two-step process
echo "Looking up PR for failed workflow run..."

PR_NUMBER=$(gh run view "$FAILED_RUN_ID" \
  --repo "$REPO" \
  --json pullRequests --jq '.pullRequests[0].number // empty' 2>/dev/null || true)

if [[ -z "$PR_NUMBER" ]]; then
  echo "No PR associated with workflow run: $FAILED_RUN_ID"
  echo "Exiting without posting comment."
  exit 0
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

# Check for duplicate comments using gh pr view --json comments with jq filtering
echo "Checking for existing duplicate comments..."
EXISTING_COMMENT=$(gh pr view "$PR_NUMBER" --repo "$REPO" --comments \
  --json comments --jq '.comments[] | select(.body | contains("<!-- workflowbot:workflow-failure-notifier -->")) | .id' 2>/dev/null || echo "")

DUPLICATE_EXISTS=false
if [[ -n "$EXISTING_COMMENT" ]]; then
  DUPLICATE_EXISTS=true
  echo "Found existing duplicate comment (ID: $EXISTING_COMMENT)"
else
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
