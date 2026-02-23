# Bot Inactivity Unassign - Test Documentation

## Overview

This document describes the test suite for `bot-inactivity-unassign.sh`, which automatically closes stale pull requests and unassigns inactive users from issues.

## Test File

**Location:** `.github/scripts/test-bot-inactivity-unassign.sh`

## Running the Tests

### Prerequisites

- Bash shell (zsh or bash)
- `jq` command-line JSON processor
- Execute permissions on the test file

### Execute Tests

```bash
cd .github/scripts
./test-bot-inactivity-unassign.sh
```

Or from the project root:

```bash
.github/scripts/test-bot-inactivity-unassign.sh
```

## Test Cases

### Test 1: PR with 'discussion' label should not be closed

**Purpose:** Verify that PRs with the 'discussion' label are preserved regardless of inactivity.

**Scenario:**
- PR #100 is open
- PR has the 'discussion' label
- PR has stale commits (25+ days old)

**Expected Result:**
- ✓ Discussion label is detected
- ✓ PR is NOT closed
- ✓ User is NOT unassigned

**Acceptance Criteria:**
- The script correctly identifies the 'discussion' label
- The PR remains open despite inactivity
- Appropriate log message: `[SKIP] PR #100 has 'discussion' label, keeping open`

---

### Test 2: Stale PR without 'discussion' label should be closed

**Purpose:** Verify that stale PRs without the 'discussion' label are eligible for closure.

**Scenario:**
- PR #200 is open
- PR does NOT have the 'discussion' label
- PR has stale commits (25+ days old)

**Expected Result:**
- ✓ Discussion label is NOT detected
- ✓ PR is eligible for closure

---

### Test 3: Verify jq filter correctly identifies 'discussion' label

**Purpose:** Test the correctness of the jq query used to extract label names.

**Scenario A:**
- PR #300 has the 'discussion' label among other labels

**Expected Result:**
- ✓ jq filter returns "discussion"

**Scenario B:**
- PR #301 does NOT have the 'discussion' label

**Expected Result:**
- ✓ jq filter returns empty string

**jq Command Tested:**
```bash
gh pr view "$PR_NUM" --repo "$REPO" --json labels --jq '.labels[].name | select(. == "discussion")'
```

---

### Test 4: Closed PRs should be skipped

**Purpose:** Verify that closed PRs are not processed.

**Scenario:**
- PR #400 is closed

**Expected Result:**
- ✓ PR state is correctly identified as not OPEN
- ✓ PR is skipped from further processing

---

### Test 5: Active PR (recent commits) should not be closed

**Purpose:** Verify that PRs with recent activity are preserved.

**Scenario:**
- PR #500 is open
- PR has recent commits (5 days old)

**Expected Result:**
- ✓ Commit data is retrieved
- ✓ Commit timestamp is extracted
- ✓ PR remains open (age < 21 days threshold)

---

### Test 6: Verify correct log messages are generated

**Purpose:** Ensure proper logging for monitoring and debugging.

**Scenario:**
- PR #600 has the 'discussion' label

**Expected Result:**
- ✓ Log message contains: `[SKIP] PR #600 has 'discussion' label, keeping open`

**Log Format Verified:**
```
[SKIP] PR #<number> has 'discussion' label, keeping open
```

---

### Test 7: PR with multiple labels including 'discussion'

**Purpose:** Verify label detection works when PR has multiple labels.

**Scenario:**
- PR #700 has multiple labels: `bug`, `discussion`, `priority-high`

**Expected Result:**
- ✓ Discussion label is found despite other labels present
- ✓ PR is protected from closure

---

### Test 8: Label matching is case-sensitive

**Purpose:** Verify that label matching is case-sensitive.

**Scenario:**
- PR #800 has label "Discussion" (capital D)
- Looking for "discussion" (lowercase)

**Expected Result:**
- ✓ Label is NOT matched (case-sensitive comparison)
- ✓ PR is NOT protected by the discussion label rule

**Note:** This ensures the script only protects PRs with the exact lowercase 'discussion' label.

---

## Test Architecture

### Mock System

The test suite uses a mock system to simulate GitHub CLI (`gh`) commands without making actual API calls:

1. **Mock gh Command:** A bash script that intercepts `gh` calls and returns predefined responses
2. **Mock Data Files:** JSON files containing simulated API responses
3. **Action Logging:** Records actions (closures, unassignments) for verification

### Test Environment

- **Temporary Directory:** Each test run creates an isolated temp directory
- **Mock Path:** Prepends mock directory to PATH to intercept commands
- **Cleanup:** Automatically removes temp directory after tests complete

### Mock Data Structure

```
$TEMP_DIR/
├── mocks/
│   └── gh                          # Mock gh CLI
└── gh_mock_data/
    ├── pr_100_state.json          # PR state data
    ├── pr_100_labels.json         # PR labels data
    ├── repos_*_pulls_*_commits.json  # Commit history
    └── actions.log                # Log of actions taken
```

## Test Output

### Success Output
```
==============================================
  Bot Inactivity Unassign - Test Suite
==============================================

✓ PASS: PR with discussion label detected
✓ PASS: PR with discussion label was NOT closed
...
==============================================
  Test Summary
==============================================
Total tests run:    11
Tests passed:       11
All tests passed!
```

### Failure Output
```
✗ FAIL: Test name
  → Detailed error message
```

## Exit Codes

- **0:** All tests passed
- **1:** One or more tests failed
- **Other:** Script error (permissions, missing dependencies, etc.)

## Maintenance

### Adding New Tests

1. Create a new test function following the naming pattern: `test_<description>()`
2. Set up mock data using helper functions
3. Execute the test scenario
4. Use `print_result` to report results
5. Add function call in `main()`

### Updating Mock Data

Mock data files are JSON formatted. Update them to match current GitHub API response structures.

Example PR labels structure:
```json
{
  "labels": [
    {"name": "discussion"},
    {"name": "bug"}
  ]
}
```

## Continuous Integration

### Recommended CI Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Test Inactivity Bot
  run: .github/scripts/test-bot-inactivity-unassign.sh
```

## Troubleshooting

### jq not found
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### Permission denied
```bash
chmod +x .github/scripts/test-bot-inactivity-unassign.sh
```

### Date command compatibility

The test script handles both GNU date (Linux) and BSD date (macOS) automatically.

## Related Files

- **Main Script:** `.github/scripts/bot-inactivity-unassign.sh`
- **Test Script:** `.github/scripts/test-bot-inactivity-unassign.sh`
- **Documentation:** `.github/scripts/TEST_DOCUMENTATION.md` (this file)

## Test Coverage

### Covered Scenarios
- ✓ Discussion label detection and preservation
- ✓ Stale PR identification
- ✓ Active PR preservation
- ✓ Closed PR skipping
- ✓ Label matching logic
- ✓ Case sensitivity
- ✓ Multiple labels handling
- ✓ Log message formatting

### Not Covered (Integration Testing Required)
- ⚠ Actual GitHub API interactions
- ⚠ Real PR closures and unassignments
- ⚠ Workflow integration
- ⚠ Multi-assignee scenarios
- ⚠ /working command detection
- ⚠ Full Phase 1 and Phase 2 workflows

## Success Metrics

For this test suite to be effective:

1. **All tests pass** before merging changes
2. **No regressions** when modifying the main script
3. **Discussion label** PRs are never incorrectly closed
4. **Test coverage** matches critical functionality

## Future Enhancements

Potential improvements to the test suite:

1. Integration tests with a test GitHub repository
2. Performance testing for large repositories
3. Edge case testing (network failures, malformed data)
4. Concurrent execution testing
5. End-to-end workflow simulation
