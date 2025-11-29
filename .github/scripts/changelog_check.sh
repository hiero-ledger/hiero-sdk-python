#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${REPO:-}" || -z "${BASE:-}" || -z "${HEAD:-}" ]]; then
    echo "❌ ERROR: Missing required environment variables (REPO, BASE, HEAD)."
    exit 1
fi

echo "Checking CHANGELOG.md..."
echo "Base SHA: $BASE"
echo "Head SHA: $HEAD"

gh api "repos/$REPO/contents/CHANGELOG.md?ref=$BASE" --jq '.content' | base64 -d > base.md
gh api "repos/$REPO/contents/CHANGELOG.md?ref=$HEAD" --jq '.content' | base64 -d > head.md


extract_unreleased() {
  sed -n '/^## \[Unreleased\]/,/^## \[/p' "$1" | sed '1d;$d' || true
}

extract_released() {
  sed '1,/^## \[Unreleased\]/d' "$1" || true
}

extract_unreleased base.md > base_unrel.txt
extract_unreleased head.md > head_unrel.txt

extract_released base.md > base_rel.txt
extract_released head.md > head_rel.txt

DIFF_UNREL=$(diff -u base_unrel.txt head_unrel.txt || true)
DIFF_REL=$(diff -u base_rel.txt head_rel.txt || true)


ADDED_TO_UNREL=$(echo "$DIFF_UNREL" | grep -E '^\+' | grep -v '^\+\+\+' || true)

if [[ -z "$ADDED_TO_UNREL" ]]; then
    echo "❌ FAIL: No additions detected in the [Unreleased] section."
    exit 1
fi


ADDED_TO_RELEASED=$(echo "$DIFF_REL" | grep -E '^\+' | grep -v '^\+\+\+' || true)

if [[ -n "$ADDED_TO_RELEASED" ]]; then
    echo "❌ FAIL: Additions detected in released sections (past versions)."
    echo "---- DIFF ----"
    echo "$DIFF_REL"
    exit 1
fi

DELETED_UNREL=$(echo "$DIFF_UNREL" | grep -E '^-' | grep -v '^---' || true)
DELETED_REL=$(echo "$DIFF_REL" | grep -E '^-' | grep -v '^---' || true)

if [[ -n "$DELETED_UNREL" ]] || [[ -n "$DELETED_REL" ]]; then
    echo "⚠️ WARNING: Deletions detected in CHANGELOG.md. Please verify they are intentional."

    if [[ -n "$DELETED_UNREL" ]]; then
        echo "--- Deleted in Unreleased section ---"
        echo "$DELETED_UNREL"
    fi

    if [[ -n "$DELETED_REL" ]]; then
        echo "--- Deleted in Released sections ---"
        echo "$DELETED_REL"
    fi
fi

echo "✅ PASS: CHANGELOG validation successful."
echo "Unreleased contains additions, and released sections contain no additions."
