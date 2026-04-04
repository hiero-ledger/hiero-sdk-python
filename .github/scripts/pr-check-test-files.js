#!/usr/bin/env node

const { execSync } = require("child_process");
const fs = require("fs");

// These are the directories we want to check for correct naming
const TEST_DIRS = ["tests/unit", "tests/integration", "tests/tck", "tests/fuzz"];

// These are the excluded paths and file names inside the TEST_DIRS
const IGNORED = ["tests/fuzz/support"];
const EXCEPTIONS = ["conftest.py", "__init__.py", "init.py", "mock_server.py", "utils.py"];

// Collect naming errors to report at the end
const name_errors = [];

// Use "git ls-files" to get all tracked files in the repository
const output = execSync("git ls-files", { encoding: "utf-8" });
// Split output into lines and filter out empty lines for easy manipulation
// e.g. output = "tests/unit/my_test.py\ntests/integration/other_test.py"
const files = output.split("\n").filter(Boolean);

for (const file of files) {
  // --- PATH FILTERING ---
  // Skip files that are not in any of the specified test directories
  if (!TEST_DIRS.some(dir => file.startsWith(dir))) continue;

  // Skip ignored paths (e.g. helpers)
  if (IGNORED.some(path => file.startsWith(path))) continue;

  // Now we have file paths that we need to check for correct naming
  // e.g. file = "tests/unit/my_test.py"

  // --- Correct PATH now apply NAMING checks ---

  // Extract the file name from the path
  // e.g. from file = "tests/unit/my_test.py" get name = "my_test.py"
  const name = file.split("/").pop();

  // Skip allowed special files
  if (EXCEPTIONS.includes(name)) continue;

  // Enforce naming rule on files 
  if (!name.endsWith("_test.py")) {
    console.error(`Name invalid test file: ${file}`);
    console.error(`::error file=${file}::Must end with '_test.py'`);
    name_errors.push(file);
  }
}

// Generate a summary of the results for the GitHub Actions UI
const summaryPath = process.env.GITHUB_STEP_SUMMARY;

if (summaryPath) {
  let summary = `## 🧪 Test File Naming Check\n\n`;

  if (name_errors.length === 0) {
    summary += `✅ All test files are correctly named\n`;
  } else {
    // Counts and lists all the incorrectly named test files
    summary += `❌ Found ${name_errors.length} incorrectly named test files:\n\n`;
    name_errors.forEach(f => {
      summary += `- \`${f}\`\n`;
    });
  }

  fs.appendFileSync(summaryPath, summary);
}

// Fail job if needed
if (name_errors.length > 0) {
  process.exit(1);
}