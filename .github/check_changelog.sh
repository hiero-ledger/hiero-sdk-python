#!/bin/bash
set -euo pipefail

REPO="${REPO:-}"
GH_TOKEN="${GH_TOKEN:-}"
PR_ACTOR="${PR_ACTOR:-}"

BASE="${BASE:-}"  # base commit SHA
HEAD="${HEAD:-}"  # head commit SHA
failed=0

# Skip Dependabot PRs
if [[ "$PR_ACTOR" == "dependabot[bot]" ]]; then
    echo "ℹ️ Dependabot PR detected — skipping CHANGELOG validation."
    exit 0
fi

echo "Fetching CHANGELOG.md from base ($BASE) and head ($HEAD)..."
gh api repos/$REPO/contents/CHANGELOG.md?ref=$BASE --jq '.content' | base64 -d > base.md
gh api repos/$REPO/contents/CHANGELOG.md?ref=$HEAD --jq '.content' | base64 -d > head.md

extract_unreleased() {
    awk '
    BEGIN {unrel=0}
    /^## \[Unreleased\]/ {unrel=1; next}
    /^## \[/ && unrel {exit}
    unrel
    ' "$1"
}

extract_released() {
    awk '
    BEGIN {unrel=0}
    /^## \[Unreleased\]/ {unrel=1; next}
    /^## \[/ && unrel {unrel=0}
    !unrel
    ' "$1"
}

base_unrel=$(extract_unreleased base.md)
head_unrel=$(extract_unreleased head.md)

base_released=$(extract_released base.md)
head_released=$(extract_released head.md)

# 1️⃣ Check released sections must not change
if ! diff -u <(echo "$base_released") <(echo "$head_released") >/dev/null; then
    echo "❌ ERROR: Released sections must not be modified. Only [Unreleased] can change."
    failed=1
fi

# 2️⃣ Check unreleased section must contain changes
if diff -u <(echo "$base_unrel") <(echo "$head_unrel") >/dev/null; then
    echo "❌ FAIL: No additions found in the [Unreleased] section."
    echo "Please add a changelog entry under [Unreleased]."
    failed=1
fi

# 3️⃣ Warn for deleted entries
deleted_entries=$(diff -u <(echo "$base_unrel") <(echo "$head_unrel") | grep '^-' || true)
if [[ -n "$deleted_entries" ]]; then
    echo "⚠️ Warning: Some changelog entries were removed in this PR:"
    echo "$deleted_entries" | sed 's/^-//'
    echo "Ensure deletions are intentional."
fi

# 4️⃣ Warn if [Unreleased] section is empty after changes
if [[ -z "$head_unrel" ]]; then
    echo "⚠️ Warning: [Unreleased] section is empty after your changes."
fi

if [[ $failed -eq 1 ]]; then
    echo "❌ Changelog check failed."
    exit 1
else
    echo "✅ Changelog [Unreleased] section correctly updated."
    exit 0
fi
