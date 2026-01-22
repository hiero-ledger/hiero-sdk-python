#!/bin/bash
set -euo pipefail
echo "Evaluating trigger event..."
if [[ "${GITHUB_EVENT_NAME}" == "workflow_dispatch" ]]; then
  echo "should_run=true" >> "${GITHUB_OUTPUT}"
  echo "Manual workflow dispatch detected."
  echo "- Proceeding with qualification check (dry-run mode if specified)."
  exit 0
fi
EVENT_DATA=$(cat "${GITHUB_EVENT_PATH}")
# Check for 'advanced' label
HAS_ADVANCED=$(jq -r 'any(.issue.labels[]; .name == "advanced") // false' <<< "${EVENT_DATA}")
if [[ "${HAS_ADVANCED}" != "true" ]]; then
  echo "should_run=false" >> "${GITHUB_OUTPUT}"
  echo "Advanced qualification check not required."
  echo "- Issue does not have the 'advanced' label."
  echo "- Skipping checkout and verification."
  exit 0
fi
ACTION=$(jq -r '.action // empty' <<< "${EVENT_DATA}")
if [[ "${ACTION}" == "assigned" ]]; then
  echo "should_run=true" >> "${GITHUB_OUTPUT}"
  echo "Advanced issue assigned."
  echo "- Proceeding with qualification check."
elif [[ "${ACTION}" == "labeled" ]]; then
  LABEL_NAME=$(jq -r '.label.name // empty' <<< "${EVENT_DATA}")
  if [[ "${LABEL_NAME}" == "advanced" ]]; then
    HAS_ASSIGNEE=$(jq -r '(.issue.assignees | length) > 0 // false' <<< "${EVENT_DATA}")
    if [[ "${HAS_ASSIGNEE}" == "true" ]]; then
      echo "should_run=true" >> "${GITHUB_OUTPUT}"
      echo "Advanced label added to an assigned issue."
      echo "- Proceeding with qualification check."
    else
      echo "should_run=false" >> "${GITHUB_OUTPUT}"
      echo "Advanced qualification check not required."
      echo "- Advanced label added, but issue has no assignees."
      echo "- Skipping checkout and verification."
    fi
  else
    echo "should_run=false" >> "${GITHUB_OUTPUT}"
    echo "Advanced qualification check not required."
    echo "- Labeled event, but label is not 'advanced'."
    echo "- Skipping checkout and verification."
  fi
else
  echo "should_run=false" >> "${GITHUB_OUTPUT}"
  echo "Advanced qualification check not required."
  echo "- Irrelevant event action."
  echo "- Skipping checkout and verification."
fi
