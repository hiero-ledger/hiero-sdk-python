#!/bin/bash
set -euo pipefail
# ==============================================================================
# Executes When:
#   - Run by GitHub Actions workflow: .github/workflows/pr-check-changelog.yml
#   - Triggers: pull_request events (opened, edited, synchronized) or manual runs.
#
# Goal:
#   This script enforces CHANGELOG discipline in Pull Requests.
#   It blocks merging unless:
#     1) A new changelog entry is added.
#     2) The entry is placed under [Unreleased].
#     3) The entry is under a valid subsection (e.g., ### Added, ### Fixed).
#     4) No previous changelog entries are deleted.
#
# ------------------------------------------------------------------------------
# Flow: High-Level Overview
#   1. Fetch upstream main branch to compare against PR changes.
#   2. Compute diff for CHANGELOG.md.
#   3. Detect added and deleted bullet entries.
#   4. Walk through CHANGELOG.md to verify correct placement.
#   5. Fail CI if entries are missing, misplaced, or removed.
#
# ------------------------------------------------------------------------------
# Flow: Detailed Technical Steps
#
# 1️⃣ Upstream Setup & Fetch
#   - Ensures 'upstream' remote exists (points to GITHUB_REPOSITORY).
#   - Runs: git fetch upstream main
#   - Purpose: Compare PR against canonical main branch.
#
# 2️⃣ Diff Extraction & Logging
#   - Runs: git diff upstream/main -- CHANGELOG.md
#   - Displays color-coded diff:
#       Green = Added lines
#       Red   = Removed lines
#   - Extracts:
#       * added_bullets  -> new bullet lines (+)
#       * deleted_bullets -> removed bullet lines (-)
#
# 3️⃣ Mandatory Entry Check
#   - If no new bullet entries are found:
#       → FAIL (You must update the changelog in every PR).
#
# 4️⃣ Context Tracking While Parsing File
#   Tracks current parsing state:
#     - current_release   -> version header (e.g., [Unreleased], [1.2.0])
#     - current_subtitle  -> section header (### Added, ### Fixed, etc.)
#     - in_unreleased     -> boolean flag (1 if inside [Unreleased])
#
# 5️⃣ Classification Rules
#   Condition                                  → Result
#   -------------------------------------------------------------
#   In [Unreleased] AND under subtitle         → correctly_placed  (PASS)
#   In [Unreleased] BUT no subtitle            → orphan_entries    (FAIL)
#   Under released version section             → wrong_release_entries (FAIL)
#
# 6️⃣ Deletion Detection
#   - If any existing changelog bullet lines are removed:
#       → FAIL (History must never be rewritten).
#
# 7️⃣ Exit Behavior
#   - If any failure condition is detected:
#       exit 1 (CI blocks merge)
#   - Otherwise:
#       exit 0 (PR passes changelog gate)
#
# ------------------------------------------------------------------------------
# Parameters:
#   None (script does not accept CLI arguments).
#
# Required Environment Variables:
#   - GITHUB_REPOSITORY : Used to configure upstream remote URL.
#
# Dependencies:
#   - git
#   - grep, sed (POSIX utilities)
#   - CHANGELOG.md must exist in repository root.
#
# Permissions:
#   - contents: read
#   - network access (for git fetch)
#
# Returns:
#   0 → Changelog entries valid and correctly placed.
#   1 → Missing entries, wrong placement, orphan entries, or deleted history.
# ==============================================================================

CHANGELOG="CHANGELOG.md"

# ANSI color codes
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

failed=0

# Fetch upstream
git remote get-url upstream &>/dev/null || git remote add upstream https://github.com/${GITHUB_REPOSITORY}.git
git fetch upstream main >/dev/null 2>&1

# Get raw diff (git diff may legitimately return non-zero)
# Get raw diff - handle non-zero exit from git diff when differences exist
raw_diff=$(git diff upstream/main -- "$CHANGELOG" 2>/dev/null || :)

# Show raw diff with colors
echo "=== Raw git diff of $CHANGELOG against upstream/main ==="
while IFS= read -r line; do
    if [[ $line =~ ^\+ && ! $line =~ ^\+\+\+ ]]; then
        echo -e "${GREEN}$line${RESET}"
    elif [[ $line =~ ^- && ! $line =~ ^--- ]]; then
        echo -e "${RED}$line${RESET}"
    else
        echo "$line"
    fi
done <<< "$raw_diff"
echo "================================="

# Extract added bullet lines
declare -A added_bullets=()
file_line=0
in_hunk=0

while IFS= read -r line; do
    if [[ $line =~ ^\@\@ ]]; then
        # Extract starting line number of the new file
        file_line=$(echo "$line" | sed -E 's/.*\+([0-9]+).*/\1/' || echo "0")
        in_hunk=1
        continue
    fi

    # Ignore lines until we are inside a hunk
    if [[ $in_hunk -eq 0 ]]; then
        continue
    fi

    if [[ $line =~ ^\+ && ! $line =~ ^\+\+\+ ]]; then
        content="${line#+}"
        if [[ $content =~ ^[[:space:]]*[-*] ]]; then
            added_bullets[$file_line]="$content"
        fi
        file_line=$((file_line + 1))
    elif [[ ! $line =~ ^\- ]]; then
        file_line=$((file_line + 1))
    fi
done <<< "$raw_diff"

# Extract deleted bullet lines
deleted_bullets=()
while IFS= read -r line; do
    [[ -n "$line" ]] && deleted_bullets+=("$line")
done < <(
    echo "$raw_diff" \
    | grep '^\-' \
    | grep -vE '^(--- |\+\+\+ |@@ )' \
    | sed 's/^-//' \
    | grep -E '^[[:space:]]*[-*]' \
    || true
)

# Warn if no added entries
if [[ ${#added_bullets[@]} -eq 0 ]]; then
    echo -e "${RED}❌ No new changelog entries detected in this PR.${RESET}"
    echo -e "${YELLOW}⚠️ Please add an entry in [Unreleased] under the appropriate subheading.${RESET}"
    failed=1
fi

# Initialize results
correctly_placed=""
orphan_entries=""
wrong_release_entries=""

# Walk through changelog to classify entries
line_no=0
current_release=""
current_subtitle=""
in_unreleased=0

while IFS= read -r line; do
    line_no=$((line_no + 1))

    if [[ $line =~ ^[[:space:]]*##\ \[Unreleased\] ]]; then
        current_release="Unreleased"
        in_unreleased=1
        current_subtitle=""
        continue
    elif [[ $line =~ ^[[:space:]]*##\ \[.*\] ]]; then
        current_release="$line"
        in_unreleased=0
        current_subtitle=""
        continue
    elif [[ $line =~ ^[[:space:]]*### ]]; then
        current_subtitle=$(echo "$line" | tr -d '\r')
        continue
    fi

    # Skip non-bullet lines for the purposes of our check
    if [[ ! $line =~ ^[[:space:]]*[-*] ]]; then
        continue
    fi

    if [[ -n "${added_bullets[$line_no]:-}" ]]; then
        added="${added_bullets[$line_no]}"

        if [[ "$in_unreleased" -eq 0 ]]; then
            wrong_release_entries+="$added   (added under released version $current_release)"$'\n'
            failed=1
        elif [[ -z "$current_subtitle" ]]; then
            orphan_entries+="$added   (NOT under a subtitle)"$'\n'
            failed=1
        else
            correctly_placed+="$added   (placed under $current_subtitle)"$'\n'
        fi
    fi
done < "$CHANGELOG"

# Display results
if [[ -n "$orphan_entries" ]]; then
    echo -e "${RED}❌ Some CHANGELOG entries are not under a subtitle in [Unreleased]:${RESET}"
    echo "$orphan_entries"
    failed=1
fi

if [[ -n "$wrong_release_entries" ]]; then
    echo -e "${RED}❌ Some changelog entries were added under a released version (should be in [Unreleased]):${RESET}"
    echo "$wrong_release_entries"
    failed=1
fi

if [[ -n "$correctly_placed" ]]; then
    echo -e "${GREEN}✅ Some CHANGELOG entries are correctly placed under [Unreleased]:${RESET}"
    echo "$correctly_placed"
fi

# Display deleted entries 
if [[ ${#deleted_bullets[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️ Changelog entries removed in this PR:${RESET}"
    for deleted in "${deleted_bullets[@]}"; do
        echo -e "  - ${YELLOW}$deleted${RESET}"
    done
    echo -e "${YELLOW}⚠️ Please add these entries back under the appropriate sections${RESET}"
fi

# Exit
if [[ $failed -eq 1 ]]; then
    echo -e "${RED}❌ Changelog check failed.${RESET}"
    exit 1
else
    echo -e "${GREEN}✅ Changelog check passed.${RESET}"
    exit 0
fi