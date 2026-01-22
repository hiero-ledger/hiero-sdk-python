#!/bin/bash
set -euo pipefail

# Validate required environment variables
: "${GITHUB_EVENT_NAME:?Missing GITHUB_EVENT_NAME}"
: "${GITHUB_OUTPUT:?Missing GITHUB_OUTPUT}"
: "${GITHUB_EVENT_PATH:?Missing GITHUB_EVENT_PATH}"

echo "Evaluating trigger event..."

# Load event data early (needed for context extraction in all paths)
EVENT_DATA=$(cat "${GITHUB_EVENT_PATH}")

# Extract contextual info with safe fallbacks (N/A for workflow_dispatch or missing fields)
ISSUE_NUMBER=$(jq -r '.issue.number // "N/A"' <<< "${EVENT_DATA}")
ACTOR=$(jq -r '.actor.login // "N/A"' <<< "${EVENT_DATA}")

# Always log context header — appears in every run for easy troubleshooting
echo "Context: Trigger=${GITHUB_EVENT_NAME} | Issue=#${ISSUE_NUMBER} | Actor=@${ACTOR}"

if [[ "${GITHUB_EVENT_NAME}" == "workflow_dispatch" ]]; then
  echo "should_run=true" >> "${GITHUB_OUTPUT}"
  echo "Manual workflow dispatch detected by @${ACTOR}."
  echo "- Proceeding with qualification check (dry-run mode if specified)."
  exit 0
fi

# Check for 'advanced' label
HAS_ADVANCED=$(jq -r 'any(.issue.labels[]; .name == "advanced") // false' <<< "${EVENT_DATA}")

if [[ "${HAS_ADVANCED}" != "true" ]]; then
  echo "should_run=false" >> "${GITHUB_OUTPUT}"
  echo "Advanced qualification check not required for issue #${ISSUE_NUMBER}."
  echo "- Issue does not have the 'advanced' label."
  echo "- Skipping checkout and verification."
  exit 0
fi

ACTION=$(jq -r '.action // empty' <<< "${EVENT_DATA}")

if [[ "${ACTION}" == "assigned" ]]; then
  echo "should_run=true" >> "${GITHUB_OUTPUT}"
  echo "Advanced issue #${ISSUE_NUMBER} assigned (triggered by @${ACTOR})."
  echo "- Proceeding with qualification check."
elif [[ "${ACTION}" == "labeled" ]]; then
  LABEL_NAME=$(jq -r '.label.name // empty' <<< "${EVENT_DATA}")
  if [[ "${LABEL_NAME}" == "advanced" ]]; then
    HAS_ASSIGNEE=$(jq -r '(.issue.assignees | length) > 0 // false' <<< "${EVENT_DATA}")
    if [[ "${HAS_ASSIGNEE}" == "true" ]]; then
      echo "should_run=true" >> "${GITHUB_OUTPUT}"
      echo "Advanced label added to assigned issue #${ISSUE_NUMBER} (by @${ACTOR})."
      echo "- Proceeding with qualification check."
    else
      echo "should_run=false" >> "${GITHUB_OUTPUT}"
      echo "Advanced qualification check not required for issue #${ISSUE_NUMBER}."
      echo "- Advanced label added by @${ACTOR}, but issue has no assignees."
      echo "- Skipping checkout and verification."
    fi
  else
    echo "should_run=false" >> "${GITHUB_OUTPUT}"
    echo "Advanced qualification check not required for issue #${ISSUE_NUMBER}."
    echo "- Labeled event by @${ACTOR}, but label is not 'advanced'."
    echo "- Skipping checkout and verification."
  fi
else
  echo "should_run=false" >> "${GITHUB_OUTPUT}"
  echo "Advanced qualification check not required for issue #${ISSUE_NUMBER}."
  echo "- Irrelevant event action (${ACTION:-none}) by @${ACTOR}."
  echo "- Skipping checkout and verification."
fi
