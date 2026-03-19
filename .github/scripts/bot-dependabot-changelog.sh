#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# bot-dependabot-changelog.sh
# =============================================================================
# Purpose:    Automatically parse a Dependabot PR title, generate a conventional
#             changelog entry, and insert it as the first bullet under the
#             appropriate section in CHANGELOG.md (under ## [Unreleased]).
#             Supports dry-run mode for safe testing.
#
# Usage:      Called from GitHub Actions workflow with environment variables:
#             PR_TITLE        - The Dependabot PR title (e.g. "Bump X from Y to Z")
#             PR_NUMBER       - PR number (for linking in entry)
#             BRANCH_NAME     - Branch name (used to determine section)
#             DRY_RUN         - "true" to log only, "false" to edit file
#
# Exit codes: 0 = success (or skipped safely)
#             1 = failure (e.g. perl edit failed)
#
# Dependencies: perl (for in-place multi-line editing), bash ≥4
# =============================================================================

# ────────────────────────────────────────────────────────────────
# Required environment variables
# ────────────────────────────────────────────────────────────────
: "${PR_TITLE:?Missing PR_TITLE}"
: "${PR_NUMBER:?Missing PR_NUMBER}"
: "${BRANCH_NAME:?Missing BRANCH_NAME}"
: "${DRY_RUN:-false}"

CHANGELOG_FILE="CHANGELOG.md"

log() {
    echo "[dependabot-changelog] $1" >&2
}

# ────────────────────────────────────────────────────────────────
# Parse Dependabot title → chore: bump ... (#PR)
# Expects: PR_TITLE, PR_NUMBER (env vars)
# Sets:    $entry (global variable with formatted changelog line)
# Exits:   0 if title doesn't match pattern (skips silently)
# ────────────────────────────────────────────────────────────────
if [[ "$PR_TITLE" =~ ^Bump\ ([^[:space:]]+)\ from\ ([^[:space:]]+)\ to\ ([^[:space:]]+)$ ]]; then
    pkg="${BASH_REMATCH[1]}"
    old="${BASH_REMATCH[2]}"
    new="${BASH_REMATCH[3]}"

    entry="chore: bump $pkg from $old to $new (#$PR_NUMBER)"

    log "Generated changelog entry:"
    log "  $entry"
else
    log "PR title does not match expected pattern 'Bump X from Y to Z'"
    log "Skipping changelog update."
    exit 0
fi

# ────────────────────────────────────────────────────────────────
# Decide section based on branch prefix
# Expects: BRANCH_NAME (env var)
# Sets:    $target_section ("### .github" or "### Src")
# ────────────────────────────────────────────────────────────────
if [[ "$BRANCH_NAME" == dependabot/github-actions/* ]]; then
    target_section="### .github"
elif [[ "$BRANCH_NAME" == dependabot/pip/* ]]; then
    target_section="### Src"
else
    log "Warning: unrecognized branch prefix → falling back to ### Src"
    target_section="### Src"
fi

log "Target section: $target_section"

# ────────────────────────────────────────────────────────────────
# Dry-run mode
# Expects: DRY_RUN="true" (env var)
# Exits:   0 after logging
# ────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] Would insert the following bullet as first entry under $target_section:"
    log "  - $entry"
    log "No changes written to $CHANGELOG_FILE"
    exit 0
fi

# ────────────────────────────────────────────────────────────────
# Real mode: insert entry into CHANGELOG.md using perl in-place edit
# Expects: $entry, $target_section (shell vars)
# Creates: CHANGELOG.md.bak (backup, removed on success)
# Modifies: CHANGELOG.md — inserts bullet under correct section in [Unreleased]
# Exits:   1 if perl fails (backup preserved)
# ────────────────────────────────────────────────────────────────
if ENTRY="$entry" TARGET_SECTION="$target_section" perl -i.bak -0777 -pe '
    my $entry = $ENV{ENTRY};
    my $target_section = $ENV{TARGET_SECTION};

    # Match ## [Unreleased] block
    if (m{## \[Unreleased\](.*?)(?=^##\s|\z)}ms) {
        my $block = $1;

        # Look for the target ### section inside the block
        if ($block =~ m{^###\s+\Q$target_section\E\s*\n(.*?)(?=^###\s|\z)}ms) {
            # Section exists → insert right after the ### line
            s{^###\s+\Q$target_section\E\s*\n}{$&\n- $entry\n};
        } else {
            # Section missing → append new subsection + bullet at end of [Unreleased]
            s{(## \[Unreleased\].*?)(\n##\s|\z)}{
                $1 . "\n$target_section\n- $entry" . $2
            }mse;
        }
    } else {
        # No [Unreleased] → append at end
        $_ .= "\n## [Unreleased]\n$target_section\n- $entry\n";
    }
' "$CHANGELOG_FILE"; then
    rm -f "${CHANGELOG_FILE}.bak"
    log "Successfully updated $CHANGELOG_FILE"
else
    log "Error: perl edit failed — backup preserved as ${CHANGELOG_FILE}.bak"
    exit 1
fi
