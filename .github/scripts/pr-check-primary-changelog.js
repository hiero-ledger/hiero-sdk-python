// Triggered only when CHANGELOG.md is modified in a PR
// This script validates that all added lines are properly placed under [Unreleased] inside a subtitle.

const { execSync } = require("child_process");
const fs = require("fs");

const CHANGELOG = "CHANGELOG.md";

function validateChangelog(fileLines, addedLines) {
    // Tracks whether we are currently inside the "Unreleased" section and subtitle
    // Starts false or "" because we begin scanning from the top of the file.
    if (addedLines.length === 0) {
        console.log("❌ CHANGELOG.md was not updated in this PR");
        process.exit(1);
    }
    let inUnreleased = false;
    let currentSubtitle = "";

    // Collects entries that violate placement rules.
    const errors = [];
    // Collects entries that are correctly placed.
    const valid = [];

    // Iterate through the entire changelog line-by-line.
    for (const raw of fileLines) {
        const line = raw.trim(); // normalize leading/trailing whitespace

        // --- SECTION TRACKING ---

        // Entering the "[Unreleased]" section:
        // This is the only valid location for new changelog entries.
        if (line.startsWith("## [Unreleased]")) {
            inUnreleased = true;
            currentSubtitle = ""; // reset subtitle until a new one is found
            continue;
        }

        // Entering any versioned (released) section:
        // Example: "## [1.2.3]" or "## [1.2.3] - 2026-03-01"
        if (/^## \[[^\]]+\]/.test(line)) {
            inUnreleased = false;
            currentSubtitle = ""; // subtitles reset per section
            continue;
        }

        // --- SUBTITLE TRACKING ---

        // Detect subsection headers (e.g. "### Added", "### Fixed").
        // Required to ensure entries are categorized properly.
        if (line.startsWith("### ")) {
            currentSubtitle = line;
            continue;
        }

        // --- LINE NORMALIZATION ---
        // Remove trailing whitespace to avoid false mismatches.
        const normalized = line.replace(/\s+$/, "");

        // --- MATCH AGAINST ADDED LINES ---

        // Only validate lines that were actually introduced in this diff.
        for (const added of addedLines) {
            if (normalized === added) {

                // Case 1: Entry is NOT inside [Unreleased]
                // → invalid (modifying historical changelog)
                if (!inUnreleased) {
                    errors.push(added);

                    // Case 2: Entry is inside [Unreleased] but not under a subtitle
                    // → invalid (uncategorized entry)
                } else if (!currentSubtitle) {
                    errors.push(added);

                    // Case 3: Entry is correctly placed
                    // → inside [Unreleased] AND under a subtitle
                } else {
                    valid.push(added);
                }
            }
        }
    }

    // Return classification results for caller (CI or tests)
    return { errors, valid };
}

function runCI() {

    // --- Extract PR diff for CHANGELOG.md ---
    let diff;
    try {
        diff = execSync(
            `git diff origin/${process.env.GITHUB_BASE_REF}...HEAD -- ${CHANGELOG}`,
            { encoding: "utf-8" }
        );
    } catch (e) {
        console.error("❌ Failed to get git diff");
        process.exit(1);
    }

    // --- Extract added bullet lines to the CHANGELOG.md ---
    // We want to know all lines added to the changelog, to later see if they are in the right place.

    const addedLines = diff
        .split("\n")
        .filter(line => line.startsWith("+") && !line.startsWith("+++"))
        .map(line => line.slice(1).trim())
        .filter(line => /^[-*]\s+/.test(line)); // only bullets

    if (addedLines.length === 0) {
        console.log("⚠️ No changelog entries found in diff");
        process.exit(0); // assume earlier step enforces presence
    }

    // --- Read the entire CHANGELOG.md  ---
    // We are next going to compare the added lines with the structure of the changelog, to see if the lines are added in the right place
    if (!fs.existsSync(CHANGELOG)) {
        console.error("❌ CHANGELOG.md not found");
        process.exit(1);
    }
    const fileLines = fs.readFileSync(CHANGELOG, "utf-8").split("\n");

    const { errors, valid } = validateChangelog(fileLines, addedLines);


    // --- Present the Output  ---
    // Note: new releases do require the creation of new subheadings and one bullet point
    // Note: this will not error if deleted lines are present
    // Note: this will not error if a new release section is created

    if (valid.length) {
        console.log("✅ Valid entries:");
        console.log(valid.join("\n"));
    }

    if (errors.length) {
        console.log("\n❌ Invalid entries:");
        console.log(errors.join("\n"));
        process.exit(1);
    }

    console.log("\n✅ All changelog entries correctly placed");
    process.exit(0);
}

if (require.main === module) {
    runCI();
}
module.exports = { validateChangelog };