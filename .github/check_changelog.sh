#!/bin/bash

CHANGELOG="CHANGELOG.md"

# ANSI color codes
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

failed=0

# Fetch upstream
git remote add upstream https://github.com/${GITHUB_REPOSITORY}.git
git fetch upstream main >/dev/null 2>&1

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
    echo -e "${YELLOW}⚠️ Please add an entry in [UNRELEASED] under the appropriate subheading.${RESET}"
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

while IFS= read -r line; do
    # Track release sections
    if [[ $line =~ ^##\ \[Unreleased\] ]]; then
        current_release="Unreleased"
        in_unreleased=1
        current_subtitle=""
        continue
    elif [[ $line =~ ^##\ \[.*\] ]]; then
        current_release="$line"
        in_unreleased=0
        current_subtitle=""
        continue
    elif [[ $line =~ ^### ]]; then
        current_subtitle="$line"
        continue
    fi

    # Check each added bullet
    for added in "${added_bullets[@]}"; do
        if [[ "$line" == "$added" ]]; then
            if [[ "$in_unreleased" -eq 1 && -n "$current_subtitle" ]]; then
                correctly_placed+="$added   (placed under $current_subtitle)"$'\n'
            elif [[ "$in_unreleased" -eq 1 && -z "$current_subtitle" ]]; then
                orphan_entries+="$added   (NOT under a subtitle)"$'\n'
            elif [[ "$in_unreleased" -eq 0 ]]; then
                wrong_release_entries+="$added   (added under released version $current_release)"$'\n'
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