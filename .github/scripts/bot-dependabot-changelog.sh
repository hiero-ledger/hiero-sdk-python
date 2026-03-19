set -euo pipefail

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
# ────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] Would insert the following bullet as first entry under $target_section:"
    log "  - $entry"
    log "No changes written to $CHANGELOG_FILE"
    exit 0
fi

# ────────────────────────────────────────────────────────────────
# Real mode
# ────────────────────────────────────────────────────────────────
perl -i.bak -0777 -pe '
    # Match ## [Unreleased] block
    if (m{## \[Unreleased\](.*?)(?=^##\s|\z)}ms) {
        my $block = $1;

        # Look for the target ### section inside the block
        if ($block =~ m{^###\s+\Q'"$target_section"'\E\s*\n(.*?)(?=^###\s|\z)}ms) {
            # Section exists → insert right after the ### line
            s{^###\s+\Q'"$target_section"'\E\s*\n}{$&\n- '"$entry"'\n};
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
' "$CHANGELOG_FILE"

log "Successfully updated $CHANGELOG_FILE"