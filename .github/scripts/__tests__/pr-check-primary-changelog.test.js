// .github/scripts/changelog-check.test.js

const fs = require("fs");
const { validateChangelog } = require("../pr-check-primary-changelog");

// Load the REAL CHANGELOG.md so tests reflect actual structure
const base = fs.readFileSync("CHANGELOG.md", "utf-8").split("\n");

/* =========================================================
   HELPERS
========================================================= */

// Create a fresh copy for each test (avoid mutation between tests)
function clone() {
    return [...base];
}

// Insert a line after a matching predicate
function insertAfter(lines, predicate, entry) {
    const idx = lines.findIndex(predicate);
    if (idx === -1) throw new Error("Insertion point not found");
    lines.splice(idx + 1, 0, entry);
}

// Safely insert under a subtitle within [Unreleased]
// Ensures we never accidentally insert into a released section
function insertUnderUnreleasedSubtitle(lines, entry) {
    let inUnreleased = false;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        if (line.startsWith("## [Unreleased]")) {
            inUnreleased = true;
            continue;
        }

        if (inUnreleased && line.startsWith("### ")) {
            lines.splice(i + 1, 0, entry);
            return;
        }

        // Stop once we leave Unreleased
        if (/^## \[[^\]]+\]/.test(line)) {
            break;
        }
    }

    throw new Error("No subtitle found under Unreleased");
}

// Minimal test runner 
function test(name, fn) {
    try {
        fn();
        console.log(`✅ ${name}`);
    } catch (e) {
        console.error(`❌ ${name}`);
        console.error("   ", e.message);
        process.exitCode = 1;
    }
}

// Simple assertion helper
function expect(condition, message) {
    if (!condition) throw new Error(message);
}

console.log("\n=== CHANGELOG VALIDATION TESTS ===\n");

/* =========================================================
   TESTS
========================================================= */

// ✅ Valid: correctly placed under [Unreleased] + subtitle
test("valid entry under Unreleased + subtitle", () => {
    const lines = clone();
    const entry = "- Added valid example";

    insertUnderUnreleasedSubtitle(lines, entry);

    const res = validateChangelog(lines, [entry]);

    expect(res.errors.length === 0, "should have no errors");
    expect(res.valid.includes(entry), "should be valid");
});

// ❌ Invalid: under [Unreleased] but missing subtitle
test("entry under Unreleased but NO subtitle", () => {
    const lines = clone();
    const entry = "- Missing subtitle";

    insertAfter(lines, l => l.startsWith("## [Unreleased]"), entry);

    const res = validateChangelog(lines, [entry]);

    expect(res.errors.includes(entry), "should be flagged as error");
    expect(res.valid.length === 0, "should not be valid");
});

// ❌ Invalid: placed under released version section
test("entry under released version", () => {
    const lines = clone();
    const entry = "- Wrong section";

    insertAfter(
        lines,
        l => /^## \[[^\]]+\]/.test(l) && !l.includes("Unreleased"),
        entry
    );

    const res = validateChangelog(lines, [entry]);

    expect(res.errors.includes(entry), "should be flagged as error");
    expect(res.valid.length === 0, "should not be valid");
});

// ⚠️ Mixed: one valid and one invalid entry
test("multiple entries mixed validity", () => {
    const lines = clone();

    const good = "- Good entry";
    const bad = "- Bad entry";

    insertUnderUnreleasedSubtitle(lines, good);
    insertAfter(
        lines,
        l => /^## \[[^\]]+\]/.test(l) && !l.includes("Unreleased"),
        bad
    );

    const res = validateChangelog(lines, [good, bad]);

    expect(res.valid.includes(good), "good should be valid");
    expect(res.errors.includes(bad), "bad should be invalid");
});

// ✅ Valid: trailing whitespace should not break matching
test("entry with trailing whitespace still matches", () => {
    const lines = clone();
    const entry = "- Trim test   ";

    insertUnderUnreleasedSubtitle(lines, entry);

    const res = validateChangelog(lines, ["- Trim test"]);

    expect(res.valid.length === 1, "should normalize whitespace");
});

// ❌ No changelog case: no entries added → validator should fail
test("no added entries", () => {
    const lines = clone();

    const res = validateChangelog(lines, []);

    expect(res.errors.length === 0, "should fail");
});

// ❌ Edge case: subtitle exists but outside Unreleased
test("subtitle outside Unreleased is invalid", () => {
    const lines = clone();
    const entry = "- Looks valid but is not";

    // Insert fake subtitle under a released section
    insertAfter(
        lines,
        l => /^## \[[^\]]+\]/.test(l) && !l.includes("Unreleased"),
        "### Fake"
    );

    insertAfter(lines, l => l === "### Fake", entry);

    const res = validateChangelog(lines, [entry]);

    expect(res.errors.includes(entry), "should still be invalid");
});


console.log("\nDone.\n");