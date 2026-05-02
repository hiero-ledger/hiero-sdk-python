// Runs examples in two phases:
// 1. Changed examples (from git diff) — fast feedback on your changes
// 2. Remaining examples (only if phase 1 passes) — full regression check

const { execSync, spawnSync } = require("child_process");

// -----------------------------
// Helpers
// -----------------------------

// Get all example files — mirrors the git ls-files pattern used in pr-check-test-files.js
function getAllExamples() {
    return execSync("git ls-files examples", { encoding: "utf-8" })
        .split("\n")
        .filter(f => f.endsWith(".py") && !f.endsWith("__init__.py"));
}

// Get changed example files (PR only)
function getChangedExamples() {
    const base = process.env.GITHUB_BASE_REF;
    if (!base) return [];
    try {
        execSync(`git fetch origin ${base}`, { encoding: "utf-8" });
        const diff = execSync(
            `git diff --name-only origin/${base}...HEAD`,
            { encoding: "utf-8" }
        ).trim();
        return diff
            ? diff.split("\n").filter(f => f.startsWith("examples/") && f.endsWith(".py"))
            : [];
    } catch {
        return [];
    }
}

// Convert file path → Python module name
function toModule(file) {
    return file.replace(/\.py$/, "").replace(/\//g, ".");
}

// Run a single example — uses spawnSync with an argument array to avoid shell injection
function runExample(file) {
    console.log(`\n************ ${file} ************`);

    const module = toModule(file);
    const result = spawnSync("uv", ["run", "-m", module], {
        stdio: "inherit",
        env: { ...process.env, PYTHONPATH: process.env.PYTHONPATH || process.cwd() },
    });

    if (result.status !== 0) {
        console.error(`\n❌ Example failed: ${file}`);
        process.exit(1);
    }

    console.log(`✅ Completed ${file}`);
}

// Run a list of examples, stopping on the first failure
function runAll(files) {
    for (const f of files) {
        runExample(f);
    }
}

// Split all examples into changed vs remaining
function computeExecutionPlan(all, changed) {
    const changedSet = new Set(changed);
    const remaining = all.filter(f => !changedSet.has(f));
    return { changed, remaining };
}

// -----------------------------
// Main logic
// -----------------------------
if (require.main === module) {
    const all = getAllExamples();
    const changed = getChangedExamples();
    const { remaining } = computeExecutionPlan(all, changed);

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

module.exports = { toModule, getAllExamples, getChangedExamples, runExample, runAll, computeExecutionPlan };
