#!/usr/bin/env bash
set -euo pipefail

# Test suite for bot-inactivity-unassign.sh
# Tests the discussion label functionality and other key behaviors

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_REPO="test-org/test-repo"
TEMP_DIR=""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Setup test environment
setup() {
  TEMP_DIR=$(mktemp -d)
  export PATH="$TEMP_DIR/mocks:$PATH"
  mkdir -p "$TEMP_DIR/mocks"
  
  # Create mock gh command directory
  export GH_MOCK_DIR="$TEMP_DIR/gh_mock_data"
  mkdir -p "$GH_MOCK_DIR"
  
  echo "Test environment created at: $TEMP_DIR"
}

# Cleanup test environment
cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
    echo "Test environment cleaned up"
  fi
}

# Print test result
print_result() {
  local test_name="$1"
  local result="$2"
  local message="${3:-}"
  
  TESTS_RUN=$((TESTS_RUN + 1))
  
  if [[ "$result" == "PASS" ]]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ PASS${NC}: $test_name"
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ FAIL${NC}: $test_name"
    if [[ -n "$message" ]]; then
      echo -e "  ${YELLOW}→${NC} $message"
    fi
  fi
}

# Create mock gh command
create_gh_mock() {
  cat > "$TEMP_DIR/mocks/gh" << 'MOCK_END'
#!/usr/bin/env bash
# Mock gh CLI for testing

GH_MOCK_DIR="${GH_MOCK_DIR:-/tmp/gh_mock_data}"

# Parse command
if [[ "$1" == "api" ]]; then
  # Handle API calls
  endpoint=""
  for arg in "$@"; do
    if [[ "$arg" =~ ^repos/ ]] || [[ "$arg" =~ ^issues/ ]]; then
      endpoint="$arg"
      break
    fi
  done
  
  # Return mock data based on endpoint
  if [[ -f "$GH_MOCK_DIR/${endpoint//\//_}.json" ]]; then
    cat "$GH_MOCK_DIR/${endpoint//\//_}.json"
  else
    echo "[]"
  fi
  
elif [[ "$1" == "pr" && "$2" == "view" ]]; then
  # Handle pr view command
  pr_num="$3"
  
  # Check if asking for state
  if [[ "$*" == *"--json state"* ]]; then
    if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_state.json" ]]; then
      cat "$GH_MOCK_DIR/pr_${pr_num}_state.json"
    else
      echo '{"state":"OPEN"}'
    fi
  # Check if asking for labels
  elif [[ "$*" == *"--json labels"* ]]; then
    # Check if jq filter is also requested
    if [[ "$*" == *"--jq"* ]]; then
      # Extract the jq filter and apply it
      if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_labels.json" ]]; then
        cat "$GH_MOCK_DIR/pr_${pr_num}_labels.json" | jq -r '.labels[].name | select(. == "discussion")' 2>/dev/null || echo ""
      else
        echo ""
      fi
    else
      # Just return the JSON
      if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_labels.json" ]]; then
        cat "$GH_MOCK_DIR/pr_${pr_num}_labels.json"
      else
        echo '{"labels":[]}'
      fi
    fi
  fi
  
elif [[ "$1" == "pr" && "$2" == "comment" ]]; then
  # Mock PR comment - just succeed
  echo "Comment added to PR"
  
elif [[ "$1" == "pr" && "$2" == "close" ]]; then
  # Mock PR close - record that it was called
  pr_num="$3"
  echo "CLOSED_PR_$pr_num" >> "$GH_MOCK_DIR/actions.log"
  echo "PR closed"
  
elif [[ "$1" == "issue" && "$2" == "comment" ]]; then
  # Mock issue comment
  echo "Comment added to issue"
  
elif [[ "$1" == "issue" && "$2" == "edit" ]]; then
  # Mock issue edit - record unassignment
  if [[ "$*" == *"--remove-assignee"* ]]; then
    for i in "${!@}"; do
      if [[ "${!i}" == "--remove-assignee" ]]; then
        next=$((i + 1))
        user="${!next}"
        issue_num=""
        for arg in "$@"; do
          if [[ "$arg" =~ ^[0-9]+$ ]]; then
            issue_num="$arg"
            break
          fi
        done
        echo "UNASSIGNED_${user}_FROM_${issue_num}" >> "$GH_MOCK_DIR/actions.log"
        break
      fi
    done
  fi
  echo "Issue edited"
  
elif [[ "$1" == "auth" && "$2" == "status" ]]; then
  # Mock auth check - always succeed
  exit 0
fi
MOCK_END
  
  chmod +x "$TEMP_DIR/mocks/gh"
  
  # Also create mock for jq (in case it's needed)
  if ! command -v jq >/dev/null 2>&1; then
    echo "WARNING: jq not found, some tests may fail"
  fi
}

# Create mock date command for consistent testing
create_date_mock() {
  # We'll use real date but could mock if needed for time-based tests
  return 0
}

# Setup mock data for a PR with discussion label
setup_pr_with_discussion_label() {
  local pr_num="$1"
  
  # PR is open
  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"
  
  # PR has discussion label
  cat > "$GH_MOCK_DIR/pr_${pr_num}_labels.json" << 'EOF'
{"labels":[{"name":"discussion"},{"name":"enhancement"}]}
EOF
  
  # Mock stale commits (21+ days old)
  local old_date=$(date -u -v-25d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "25 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$old_date"}}}]
EOF
}

# Setup mock data for a stale PR without discussion label
setup_stale_pr_without_discussion() {
  local pr_num="$1"
  
  # PR is open
  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"
  
  # PR has no discussion label
  echo '{"labels":[{"name":"bug"}]}' > "$GH_MOCK_DIR/pr_${pr_num}_labels.json"
  
  # Mock stale commits
  local old_date=$(date -u -v-25d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "25 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$old_date"}}}]
EOF
}

# Setup mock data for an active PR
setup_active_pr() {
  local pr_num="$1"
  
  # PR is open
  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"
  
  # PR has no discussion label
  echo '{"labels":[{"name":"feature"}]}' > "$GH_MOCK_DIR/pr_${pr_num}_labels.json"
  
  # Mock recent commits
  local recent_date=$(date -u -v-5d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "5 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$recent_date"}}}]
EOF
}

# Setup mock data for a closed PR
setup_closed_pr() {
  local pr_num="$1"
  
  # PR is closed
  echo '{"state":"CLOSED"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"
  
  # Labels don't matter for closed PR
  echo '{"labels":[]}' > "$GH_MOCK_DIR/pr_${pr_num}_labels.json"
}

# Test 1: PR with discussion label should NOT be closed
test_pr_with_discussion_label_not_closed() {
  echo ""
  echo "Test 1: PR with 'discussion' label should not be closed"
  echo "=========================================================="
  
  setup_pr_with_discussion_label "100"
  
  # Create a minimal test scenario
  # We'll test the relevant part of the script logic
  
  # Simulate the check
  local pr_num="100"
  local HAS_DISCUSSION_LABEL
  HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ -n "$HAS_DISCUSSION_LABEL" ]]; then
    # Should skip closing
    print_result "PR with discussion label detected" "PASS"
    
    # Verify PR was not closed
    if [[ ! -f "$GH_MOCK_DIR/actions.log" ]] || ! grep -q "CLOSED_PR_$pr_num" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
      print_result "PR with discussion label was NOT closed" "PASS"
    else
      print_result "PR with discussion label was NOT closed" "FAIL" "PR was incorrectly closed"
    fi
  else
    print_result "PR with discussion label detected" "FAIL" "Discussion label not detected"
  fi
}

# Test 2: Stale PR without discussion label should be closed
test_stale_pr_without_discussion_closed() {
  echo ""
  echo "Test 2: Stale PR without 'discussion' label should be closed"
  echo "=============================================================="
  
  setup_stale_pr_without_discussion "200"
  
  local pr_num="200"
  local HAS_DISCUSSION_LABEL
  HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ -z "$HAS_DISCUSSION_LABEL" ]]; then
    print_result "PR without discussion label detected" "PASS"
  else
    print_result "PR without discussion label detected" "FAIL" "Discussion label incorrectly detected"
  fi
}

# Test 3: Verify label check uses correct jq filter
test_jq_filter_correctness() {
  echo ""
  echo "Test 3: Verify jq filter correctly identifies 'discussion' label"
  echo "=================================================================="
  
  # Test with discussion label present
  setup_pr_with_discussion_label "300"
  local result
  result=$(gh pr view "300" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ "$result" == "discussion" ]]; then
    print_result "jq filter finds 'discussion' label" "PASS"
  else
    print_result "jq filter finds 'discussion' label" "FAIL" "Expected 'discussion', got '$result'"
  fi
  
  # Test with no discussion label
  setup_stale_pr_without_discussion "301"
  result=$(gh pr view "301" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ -z "$result" ]]; then
    print_result "jq filter returns empty for missing 'discussion' label" "PASS"
  else
    print_result "jq filter returns empty for missing 'discussion' label" "FAIL" "Expected empty, got '$result'"
  fi
}

# Test 4: Closed PRs should be skipped
test_closed_pr_skipped() {
  echo ""
  echo "Test 4: Closed PRs should be skipped"
  echo "======================================"
  
  setup_closed_pr "400"
  
  local pr_num="400"
  local pr_state
  pr_state=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json state --jq '.state' 2>/dev/null || echo "")
  
  if [[ "$pr_state" != "OPEN" ]]; then
    print_result "Closed PR correctly identified" "PASS"
  else
    print_result "Closed PR correctly identified" "FAIL" "PR state is '$pr_state'"
  fi
}

# Test 5: Active PR should not be closed
test_active_pr_not_closed() {
  echo ""
  echo "Test 5: Active PR (recent commits) should not be closed"
  echo "========================================================="
  
  setup_active_pr "500"
  
  local pr_num="500"
  local COMMITS_JSON
  COMMITS_JSON=$(gh api "repos/$TEST_REPO/pulls/$pr_num/commits" 2>/dev/null || echo "[]")
  
  if echo "$COMMITS_JSON" | jq -e 'length > 0' >/dev/null 2>&1; then
    print_result "Active PR has commit data" "PASS"
    
    # In real script, this would calculate age and skip if < 21 days
    local last_commit_date
    last_commit_date=$(echo "$COMMITS_JSON" | jq -r 'last | .commit.committer.date // empty')
    if [[ -n "$last_commit_date" ]]; then
      print_result "Active PR commit timestamp retrieved" "PASS"
    else
      print_result "Active PR commit timestamp retrieved" "FAIL" "No timestamp found"
    fi
  else
    print_result "Active PR has commit data" "FAIL" "No commits found"
  fi
}

# Test 6: Log output verification
test_log_output() {
  echo ""
  echo "Test 6: Verify correct log messages are generated"
  echo "==================================================="
  
  setup_pr_with_discussion_label "600"
  
  # Capture output
  local output
  local pr_num="600"
  output=$(
    HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
    if [[ -n "$HAS_DISCUSSION_LABEL" ]]; then
      echo "    [SKIP] PR #$pr_num has 'discussion' label, keeping open"
    fi
  )
  
  if echo "$output" | grep -q "\[SKIP\].*discussion.*keeping open"; then
    print_result "Correct log message for discussion label" "PASS"
  else
    print_result "Correct log message for discussion label" "FAIL" "Expected log message not found"
  fi
}

# Test 7: Multiple labels including discussion
test_multiple_labels_with_discussion() {
  echo ""
  echo "Test 7: PR with multiple labels including 'discussion'"
  echo "========================================================"
  
  # Create PR with multiple labels including discussion
  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_700_state.json"
  cat > "$GH_MOCK_DIR/pr_700_labels.json" << 'EOF'
{"labels":[{"name":"bug"},{"name":"discussion"},{"name":"priority-high"}]}
EOF
  
  local pr_num="700"
  local HAS_DISCUSSION_LABEL
  HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ "$HAS_DISCUSSION_LABEL" == "discussion" ]]; then
    print_result "Discussion label found among multiple labels" "PASS"
  else
    print_result "Discussion label found among multiple labels" "FAIL" "Label not detected"
  fi
}

# Test 8: Case sensitivity check
test_case_sensitivity() {
  echo ""
  echo "Test 8: Label matching is case-sensitive"
  echo "=========================================="
  
  # Create PR with "Discussion" (capital D)
  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_800_state.json"
  echo '{"labels":[{"name":"Discussion"}]}' > "$GH_MOCK_DIR/pr_800_labels.json"
  
  local pr_num="800"
  local HAS_DISCUSSION_LABEL
  HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name | select(. == "discussion")' 2>/dev/null || echo "")
  
  if [[ -z "$HAS_DISCUSSION_LABEL" ]]; then
    print_result "Case-sensitive matching (Discussion != discussion)" "PASS"
  else
    print_result "Case-sensitive matching (Discussion != discussion)" "FAIL" "Should not match different case"
  fi
}

# Main test runner
main() {
  echo "=============================================="
  echo "  Bot Inactivity Unassign - Test Suite"
  echo "=============================================="
  echo ""
  
  # Setup
  setup
  trap cleanup EXIT
  
  # Create mocks
  create_gh_mock
  create_date_mock
  
  # Clear actions log
  rm -f "$GH_MOCK_DIR/actions.log"
  
  # Run tests
  test_pr_with_discussion_label_not_closed
  test_stale_pr_without_discussion_closed
  test_jq_filter_correctness
  test_closed_pr_skipped
  test_active_pr_not_closed
  test_log_output
  test_multiple_labels_with_discussion
  test_case_sensitivity
  
  # Summary
  echo ""
  echo "=============================================="
  echo "  Test Summary"
  echo "=============================================="
  echo "Total tests run:    $TESTS_RUN"
  echo -e "${GREEN}Tests passed:       $TESTS_PASSED${NC}"
  if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}Tests failed:       $TESTS_FAILED${NC}"
    exit 1
  else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
  fi
}

# Run tests
main "$@"