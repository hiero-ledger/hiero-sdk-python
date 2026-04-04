// Runs examples in two phases:
// 1. Changed examples (from git diff)
// 2. Remaining examples (only if phase 1 passes)

const { execSync } = require("child_process");
const base = process.env.GITHUB_BASE_REF;

// -----------------------------
// Helpers
// -----------------------------

function sh(cmd) {
    return execSync(cmd, { encoding: "utf-8" }).trim();
}

function safeSh(cmd) {
    try {
        return sh(cmd);
    } catch {
        return "";
    }
}

// Get all example files
function getAllExamples() {
    const out = safeSh(
        `find examples -name "*.py" -type f ! -name "__init__.py"`
    );

    return out ? out.split("\n").filter(Boolean) : [];
}

// Get changed example files (PR only)
function getChangedExamples() {
    if (!process.env.GITHUB_BASE_REF) {
        return [];
    }

    const diff = safeSh(
        `git fetch origin ${base} && git diff --name-only origin/${base}...HEAD`
    );

    return diff
        ? diff.split("\n").filter(f => f.startsWith("examples/") && f.endsWith(".py"))
        : [];
}

// Convert file path → Python module
function toModule(file) {
    return file.replace(/\.py$/, "").replace(/\//g, ".");
}

// Run a single example
function runExample(file) {
    console.log(`\n************ ${file} ************`);

    const module = toModule(file);

    try {
        execSync(`uv run -m ${module}`, {
            stdio: "inherit",
            env: process.env,
        });

        console.log(`✅ Completed ${file}`);
    } catch (err) {
        console.error(`\n❌ Example failed: ${file}`);
        process.exit(1); // fail fast
    }
}

// Run list of examples
function runAll(files) {
    for (const f of files) {
        runExample(f);
    }
}

// -----------------------------
// Main logic
// -----------------------------
if (require.main === module) {
    const all = getAllExamples();
    const changed = getChangedExamples();

    const changedSet = new Set(changed);
    const remaining = all.filter(f => !changedSet.has(f));

    console.log("\n=== Example Execution Plan ===");
    console.log("Changed:", changed.length ? changed : "(none)");
    console.log("Remaining:", remaining.length);
    console.log("");

    if (changed.length > 0) {
        console.log("🚀 Phase 1: Running CHANGED examples...");
        runAll(changed);
    } else {
        console.log("ℹ️ No changed examples detected");
    }

    if (remaining.length > 0) {
        console.log("\n🚀 Phase 2: Running remaining examples...");
        runAll(remaining);
    }

    console.log("\n✅ All examples completed successfully");
}

module.exports = {
    toModule,
    runExample,
    runAll,
    computeExecutionPlan: (all, changed) => {
        const changedSet = new Set(changed);
        const remaining = all.filter(f => !changedSet.has(f));
        return { changed, remaining };
    }
};