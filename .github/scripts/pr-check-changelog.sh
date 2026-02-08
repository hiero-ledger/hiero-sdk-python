#!/bin/bash
set -euo pipefail
# ==============================================================================
# Executes When:
#   - Run by GitHub Actions workflow: .github/workflows/pr-check-changelog.yml
#   - Triggers: workflow_dispatch (manual) and pull_request (opened, edited, synch).
#
# Goal:
#   It acts as a gatekeeper for Pull Requests, blocking any merge unless the user
#   has added a new entry to CHANGELOG.md and correctly placed it under the
#   [Unreleased] section with a proper category subtitle.
#
# ------------------------------------------------------------------------------
# Flow: Basic Idea
#   1. Grabs the official blueprints (upstream/main) to compare against current work.
#   2. Checks if anything new was written. If not, fails immediately.
#   3. Walks through the file line-by-line to ensure new notes are strictly filed
#      under [Unreleased] and organized under a category (e.g., "Added", "Fixed").
#   4. If notes are missing, misplaced, or dangling, it fails the build.
#      If filed correctly, it approves the build.
#
# ------------------------------------------------------------------------------
# Flow: Detailed Technical Steps
#
# 1️⃣ Network Setup & Fetch
#    - Action: Sets up a remote connection to GitHub and runs 'git fetch upstream main'.
#    - Why: Needs the "Source of Truth" to compare the Pull Request against.
#
# 2️⃣ Diff Analysis & Visualization
#    - Action: Runs 'git diff upstream/main -- CHANGELOG.md'.
#    - UX/Display: Prints raw diff with colors (Green=Additions, Red=Deletions)
#      strictly for human readability in logs; logic does not rely on colors.
#    - Logic: Extracts two lists:
#      * added_bullets: Every line starting with '+' (new text).
#      * deleted_bullets: Every line starting with '-' (removed text).
#    - Immediate Fail Check: If 'added_bullets' is empty, sets failed=1 and exits.
#      (You cannot merge code without a changelog entry).
#
# 3️⃣ Context Tracking 
#    As the script reads the file line-by-line, it tracks:
#    - current_release: Main version header (e.g., [Unreleased] or [1.0.0]).
#    - current_subtitle: Sub-category (e.g., ### Added, ### Fixed).
#    - in_unreleased: Flag (0 or 1).
#       * 1 (True)  -> Currently inside [Unreleased] (Safe Zone).
#       * 0 (False) -> Reading an old version (Danger Zone).
#
# 4️⃣ Sorting
#   Flag is ON (1) AND Subtitle is Set 	    -> correctly_placed    		    -> PASS ✅
#   Flag is ON (1) BUT Subtitle is Empty    -> orphan_entries       		-> FAIL ❌ (It's dangling, not under a category)
#   Flag is OFF (0)          				-> wrong_release_entries	    -> FAIL ❌ (edited old history)
#
# 5️⃣ Final Result
#    Aggregates failures from Step 4. If any FAIL buckets are not empty, exit 1.
#
# ------------------------------------------------------------------------------
# Parameters:
#   None. (The script accepts no command-line arguments).
#
# Environment Variables (Required):
#   - GITHUB_REPOSITORY: Used to fetch the upstream 'main' branch for comparison.
#
# Dependencies:
#   - git (must be able to fetch upstream)
#   - jq (required for PR context parsing)
#   - grep, sed (standard Linux utilities)
#   - CHANGELOG.md (file must exist in the root directory)
#
# Permissions:
#   - 'contents: read' (to access the file structure).
#   - Network access (to run 'git fetch upstream').
#
# Returns:
#   0 (Success) - Changes are valid and correctly placed.
#   1 (Failure) - Missing entries, wrong placement (e.g. under released version),
#                 orphan entries (no subtitle), or accidental deletions.
# ==============================================================================

CHANGELOG="CHANGELOG.md"

# Ensure jq is available (required for PR context + comments)
command -v jq >/dev/null || {
    echo "❌ jq is required but not installed"
    exit 1
}

# Validate required environment variables
: "${GITHUB_EVENT_PATH:?GITHUB_EVENT_PATH is not set}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is not set}"

# PR Number
PR_NUMBER=$(jq -r '.pull_request.number // empty' "$GITHUB_EVENT_PATH")
if [[ -n "$PR_NUMBER" ]] && ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "❌ Invalid PR_NUMBER: $PR_NUMBER"
    exit 1
fi

# GITHUB_TOKEN is only required for PR commenting
if [[ -n "$PR_NUMBER" ]]; then
    : "${GITHUB_TOKEN:?GITHUB_TOKEN is required for PR commenting but is not set}"
fi

# Marker
MISSING_MARKER="<!-- changelog-missing-bot -->"
WRONG_SECTION_MARKER="<!-- changelog-wrong-section-bot -->"

# ANSI color codes
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

failed=0

# Fetch upstream
git remote add upstream https://github.com/${GITHUB_REPOSITORY}.git
git fetch upstream main >/dev/null 2>&1

#PR Comment
DRY_RUN="${DRY_RUN:-false}"
post_pr_comment() {
    local message="$1"

    # Only comment if this is a PR (not workflow_dispatch)
    if [[ -z "$PR_NUMBER" ]]; then
        echo "ℹ️ No PR_NUMBER set — skipping comment."
        return
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🔍 [DRY RUN] Would post PR comment on #${PR_NUMBER}"
        return
    fi

    local http_code
    http_code=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments" \
        -d "$(jq -n --arg body "$message" '{body: $body}')")

    if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
        echo "⚠️ Failed to post PR comment (HTTP $http_code)"
    fi
}

comment_already_exists() {
    local marker="$1"

    if [[ -z "$PR_NUMBER" ]]; then
        return 1
    fi

    local comments
    comments=$(curl -s \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments?per_page=100")

    if ! echo "$comments" | jq -e 'type == "array"' >/dev/null 2>&1; then
        echo "⚠️ Failed to fetch PR comments — assuming marker absent"
        return 1
    fi

    echo "$comments" | jq -e --arg marker "$marker" '
        .[] | select(.body | contains($marker))
    ' >/dev/null
}

# Get raw diff
raw_diff=$(git diff upstream/main -- "$CHANGELOG")

# 1️⃣ Show raw diff with colors
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

# 2️⃣ Extract added bullet lines
added_bullets=()
while IFS= read -r line; do
    [[ -n "$line" ]] && added_bullets+=("$line")
done < <(echo "$raw_diff" | sed -n 's/^+//p' | grep -E '^[[:space:]]*[-*]' | sed '/^[[:space:]]*$/d')

# 2️⃣a Extract deleted bullet lines
deleted_bullets=()
while IFS= read -r line; do
    [[ -n "$line" ]] && deleted_bullets+=("$line")
done < <(echo "$raw_diff" | grep '^\-' | grep -vE '^(--- |\+\+\+ |@@ )' | sed 's/^-//')

# 2️⃣b Warn if no added entries
if [[ ${#added_bullets[@]} -eq 0 ]]; then
    echo -e "${RED}❌ No new changelog entries detected in this PR.${RESET}"
    echo -e "${YELLOW}⚠️ Please add an entry in [Unreleased] under the appropriate subheading.${RESET}"

    if ! comment_already_exists "$MISSING_MARKER"; then
        post_pr_comment "$MISSING_MARKER
👋 **Changelog reminder**

This PR appears to resolve an issue, but no entry was found in **CHANGELOG.md**.

📌 In this repository, all resolved issues — including docs, CI, and workflow changes — are expected to include a changelog entry under **[Unreleased]**, grouped by category (e.g. *Added*, *Fixed*).

If this PR should not require a changelog entry, feel free to clarify in the discussion. Thanks! 🙌"
    else
        echo "⚠️ Changelog bot comment already exists, skipping"
    fi

    failed=1
fi

# 3️⃣ Initialize results
correctly_placed=""
orphan_entries=""
wrong_release_entries=""

# 4️⃣ Walk through changelog to classify entries
current_release=""
current_subtitle=""
in_unreleased=0

shopt -s extglob

while IFS= read -r line; do
    # Track release sections
    if [[ $line =~ ^##\ \[Unreleased\] ]]; then
        current_release="Unreleased"
        in_unreleased=1
        current_subtitle=""
        continue
    elif [[ $line =~ ^#{1,2}\ \[([0-9]+\.[0-9]+\.[0-9]+)\] ]]; then
        current_release="${BASH_REMATCH[1]}"
        in_unreleased=0
        current_subtitle=""
        continue
    elif [[ $line =~ ^### ]]; then
        current_subtitle="$line"
        continue
    fi

    # Check each added bullet

    normalized_line="${line%%+([[:space:]])}"
    for added in "${added_bullets[@]}"; do
        normalized_added="${added%%+([[:space:]])}"

        if [[ "$normalized_line" == "$normalized_added" ]]; then
            if [[ "$in_unreleased" -eq 1 && -n "$current_subtitle" ]]; then
                correctly_placed+="$added   (placed under $current_subtitle)"$'\n'
            elif [[ "$in_unreleased" -eq 1 && -z "$current_subtitle" ]]; then
                orphan_entries+="$added   (NOT under a subtitle)"$'\n'
            elif [[ "$in_unreleased" -eq 0 ]]; then
                wrong_release_entries+="$added   (added under released version [$current_release], expected under [Unreleased])"$'\n'
            fi
        fi
    done
done < "$CHANGELOG"

# 5️⃣ Display results
if [[ -n "$orphan_entries" ]]; then
    echo -e "${RED}❌ Some CHANGELOG entries are not under a subtitle in [Unreleased]:${RESET}"
    echo "$orphan_entries"
    failed=1
fi

if [[ -n "$wrong_release_entries" ]]; then
    echo -e "${RED}❌ Some changelog entries were added under a released version (should be in [Unreleased]):${RESET}"
    echo "$wrong_release_entries"

    if ! comment_already_exists "$WRONG_SECTION_MARKER"; then
        post_pr_comment "$WRONG_SECTION_MARKER
⚠️ **Changelog placement issue**

Thanks for adding a changelog entry! 🙌  
However, one or more entries in this PR were added under a **released version**.

📌 New changelog entries should always go under **[Unreleased]**, grouped beneath an appropriate category (e.g. *Added*, *Fixed*).

Please move the following entries to **[Unreleased]**:

\`\`\`
$wrong_release_entries
\`\`\`


Let us know if you’re unsure where it should live — happy to help!"

    else
        echo "⚠️ Changelog bot comment already exists, skipping"
    fi

    failed=1
fi

if [[ -n "$correctly_placed" ]]; then
    echo -e "${GREEN}✅ Some CHANGELOG entries are correctly placed under [Unreleased]:${RESET}"
    echo "$correctly_placed"
fi

# 6️⃣ Display deleted entries
if [[ ${#deleted_bullets[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Changelog entries removed in this PR:${RESET}"
    for deleted in "${deleted_bullets[@]}"; do
        echo -e "  - ${RED}$deleted${RESET}"
    done
    echo -e "${YELLOW}⚠️ Please add these entries back under the appropriate sections${RESET}"
fi

# 7️⃣ Exit with failure if any bad entries exist
if [[ $failed -eq 1 ]]; then
    echo -e "${RED}❌ Changelog check failed.${RESET}"
    exit 1
else
    echo -e "${GREEN}✅ Changelog check passed.${RESET}"
    exit 0
fi
