#!/usr/bin/env bash
set -euo pipefail

# Test suite for bot-inactivity-unassign.sh
# Tests the discussion label functionality and other key behaviors

TEST_REPO="test-org/test-repo"
TEMP_DIR=""
BOT_SCRIPT=".github/scripts/bot-inactivity-unassign.sh"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

setup() {
  TEMP_DIR=$(mktemp -d)
  export PATH="$TEMP_DIR/mocks:$PATH"
  mkdir -p "$TEMP_DIR/mocks"

  # Create mock gh command directory
  export GH_MOCK_DIR="$TEMP_DIR/gh_mock_data"
  mkdir -p "$GH_MOCK_DIR"

  echo "Test environment created at: $TEMP_DIR"
}

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}

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
set -euo pipefail
# Mock gh CLI for testing

GH_MOCK_DIR="${GH_MOCK_DIR:-/tmp/gh_mock_data}"

# Parse command
if [[ "$1" == "api" ]]; then
  # Handle API calls
  # Accept production flags like --paginate and -H, but treat fixtures as single-page responses.
  endpoint=""
  for arg in "$@"; do
    if [[ "$arg" =~ ^repos/ ]] || [[ "$arg" =~ ^issues/ ]]; then
      endpoint="$arg"
      break
    fi
  done

  jq_filter=""
  if [[ "$*" == *"--jq"* ]]; then
    args=("$@")
    for i in "${!args[@]}"; do
      if [[ "${args[i]}" == "--jq" ]]; then
        next=$((i + 1))
        if (( next < ${#args[@]} )); then
          jq_filter="${args[next]}"
        fi
        break
      elif [[ "${args[i]}" == --jq=* ]]; then
        jq_filter="${args[i]#--jq=}"
        break
      fi
    done
  fi

  # Return mock data based on endpoint
  if [[ -f "$GH_MOCK_DIR/${endpoint//\//_}.json" ]]; then
    if [[ -n "$jq_filter" ]]; then
      cat "$GH_MOCK_DIR/${endpoint//\//_}.json" | jq -r "$jq_filter" 2>/dev/null || echo ""
    else
      cat "$GH_MOCK_DIR/${endpoint//\//_}.json"
    fi
  else
    if [[ -n "$jq_filter" ]]; then
      echo "[]" | jq -r "$jq_filter" 2>/dev/null || echo ""
    else
      echo "[]"
    fi
  fi

elif [[ "$1" == "pr" && "$2" == "view" ]]; then
  # Handle pr view command
  pr_num="$3"

  # Check if asking for state
  if [[ "$*" == *"--json state"* ]]; then
    if [[ "$*" == *"--jq"* ]]; then
      jq_filter=""
      args=("$@")
      for i in "${!args[@]}"; do
        if [[ "${args[i]}" == "--jq" ]]; then
          next=$((i + 1))
          if (( next < ${#args[@]} )); then
            jq_filter="${args[next]}"
          fi
          break
        elif [[ "${args[i]}" == --jq=* ]]; then
          jq_filter="${args[i]#--jq=}"
          break
        fi
      done

      if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_state.json" ]]; then
        if [[ -n "$jq_filter" ]]; then
          cat "$GH_MOCK_DIR/pr_${pr_num}_state.json" | jq -r "$jq_filter" 2>/dev/null || echo ""
        else
          cat "$GH_MOCK_DIR/pr_${pr_num}_state.json"
        fi
      else
        echo '{"state":"OPEN"}'
      fi
    else
      if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_state.json" ]]; then
        cat "$GH_MOCK_DIR/pr_${pr_num}_state.json"
      else
        echo '{"state":"OPEN"}'
      fi
    fi
  # Check if asking for labels
  elif [[ "$*" == *"--json labels"* ]]; then
    # Check if jq filter is also requested
    if [[ "$*" == *"--jq"* ]]; then
      # Extract the caller-provided --jq filter and apply it
      jq_filter=""
      args=("$@")
      for i in "${!args[@]}"; do
        if [[ "${args[i]}" == "--jq" ]]; then
          next=$((i + 1))
          if (( next < ${#args[@]} )); then
            jq_filter="${args[next]}"
          fi
          break
        elif [[ "${args[i]}" == --jq=* ]]; then
          jq_filter="${args[i]#--jq=}"
          break
        fi
      done

      if [[ -f "$GH_MOCK_DIR/pr_${pr_num}_labels.json" ]]; then
        if [[ -n "$jq_filter" ]]; then
          cat "$GH_MOCK_DIR/pr_${pr_num}_labels.json" | jq -r "$jq_filter" 2>/dev/null || echo ""
        else
          cat "$GH_MOCK_DIR/pr_${pr_num}_labels.json"
        fi
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
    # Copy arguments into an array for indexed access
    args=("$@")
    # Determine the issue number (first purely numeric argument)
    issue_num=""
    for arg in "${args[@]}"; do
      if [[ "$arg" =~ ^[0-9]+$ ]]; then
        issue_num="$arg"
        break
      fi
    done
    # Find the --remove-assignee flag and its following username
    user=""
    for i in "${!args[@]}"; do
      if [[ "${args[i]}" == "--remove-assignee" ]]; then
        next=$((i + 1))
        if (( next < ${#args[@]} )); then
          user="${args[next]}"
          echo "UNASSIGNED_${user}_FROM_${issue_num}" >> "$GH_MOCK_DIR/actions.log"
        fi
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

  if ! command -v jq >/dev/null 2>&1; then
    echo "WARNING: jq not found, some tests may fail"
  fi
}

# Setup full issue + timeline + PR data for executing the actual bot script
setup_issue_with_linked_pr() {
  local issue_num="$1"
  local pr_num="$2"
  local assignee="$3"

  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_issues.json" << EOF
[
  {
    "number": $issue_num,
    "state": "open",
    "assignees": [{"login": "$assignee"}]
  }
]
EOF

  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_issues_${issue_num}.json" << EOF
{
  "number": $issue_num,
  "state": "open",
  "created_at": "2026-01-01T00:00:00Z",
  "assignees": [{"login": "$assignee"}]
}
EOF

  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_issues_${issue_num}_timeline.json" << EOF
[
  {
    "event": "assigned",
    "created_at": "2026-01-02T00:00:00Z",
    "assignee": {"login": "$assignee"}
  },
  {
    "event": "cross-referenced",
    "source": {
      "issue": {
        "number": $pr_num,
        "pull_request": {"url": "https://api.github.com/repos/$TEST_REPO/pulls/$pr_num"},
        "repository": {"full_name": "$TEST_REPO"}
      }
    }
  }
]
EOF
}

setup_labeled_pr_with_linked_issue() {
  local issue_num="$1"
  local pr_num="$2"
  local assignee="$3"
  local label_name="$4"

  setup_issue_with_linked_pr "$issue_num" "$pr_num" "$assignee"

  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"
  cat > "$GH_MOCK_DIR/pr_${pr_num}_labels.json" << EOF
{"labels":[{"name":"$label_name"}]}
EOF

  local old_date
  old_date=$(date -u -v-25d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "25 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$old_date"}}}]
EOF
}

# Setup mock data for a PR with discussion label
setup_pr_with_discussion_label() {
  local pr_num="$1"

  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"

  cat > "$GH_MOCK_DIR/pr_${pr_num}_labels.json" << 'EOF'
{"labels":[{"name":"discussion"},{"name":"enhancement"}]}
EOF

  # Mock stale commits (21+ days old)
  local old_date
  old_date=$(date -u -v-25d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "25 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$old_date"}}}]
EOF
}

# Setup mock data for a stale PR without discussion label
setup_stale_pr_without_discussion() {
  local pr_num="$1"

  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"

  # PR has no discussion label
  echo '{"labels":[{"name":"bug"}]}' > "$GH_MOCK_DIR/pr_${pr_num}_labels.json"

  # Mock stale commits
  local old_date
  old_date=$(date -u -v-25d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "25 days ago" +"%Y-%m-%dT%H:%M:%SZ")
  cat > "$GH_MOCK_DIR/repos_${TEST_REPO//\//_}_pulls_${pr_num}_commits.json" << EOF
[{"commit":{"committer":{"date":"$old_date"}}}]
EOF
}

# Setup mock data for an active PR
setup_active_pr() {
  local pr_num="$1"

  echo '{"state":"OPEN"}' > "$GH_MOCK_DIR/pr_${pr_num}_state.json"

  # PR has no discussion label
  echo '{"labels":[{"name":"feature"}]}' > "$GH_MOCK_DIR/pr_${pr_num}_labels.json"

  # Mock recent commits
  local recent_date
  recent_date=$(date -u -v-5d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "5 days ago" +"%Y-%m-%dT%H:%M:%SZ")
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
  echo "Test 1: Skip stale PR with 'discussion' label"
  echo "=================================================================="

  local issue_num="1000"
  local pr_num="100"
  local assignee="alice"

  setup_issue_with_linked_pr "$issue_num" "$pr_num" "$assignee"
  setup_pr_with_discussion_label "$pr_num"

  local output
  if output=$(REPO="$TEST_REPO" DAYS=21 DRY_RUN=0 bash "$BOT_SCRIPT" 2>&1); then
    print_result "script executed with mocked data" "PASS"
  else
    print_result "script executed with mocked data" "FAIL" "Bot exited non-zero: $output"
  fi
  if grep -Eq "\\[SKIP\\].*discussion" <<<"$output"; then
    print_result "discussion-label skip log emitted" "PASS"
  else
    print_result "discussion-label skip log emitted" "FAIL" "Expected discussion-label skip log"
  fi
  if [[ ! -f "$GH_MOCK_DIR/actions.log" ]] || ! grep -q "CLOSED_PR_$pr_num" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "script did NOT close PR with discussion label" "PASS"
  else
    print_result "script did NOT close PR with discussion label" "FAIL" "PR was incorrectly closed"
  fi
  if [[ ! -f "$GH_MOCK_DIR/actions.log" ]] || ! grep -q "UNASSIGNED_${assignee}_FROM_${issue_num}" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "script did NOT unassign issue for discussion PR" "PASS"
  else
    print_result "script did NOT unassign issue for discussion PR" "FAIL" "Assignee was incorrectly removed"
  fi
}

# Test 2: Stale PR without discussion label should be closed
test_stale_pr_without_discussion_closed() {
  echo ""
  echo "Test 2: Stale PR without 'discussion' label should be closed"
  echo "=============================================================="

  local issue_num="2000"
  local pr_num="200"
  local assignee="alice"

  setup_issue_with_linked_pr "$issue_num" "$pr_num" "$assignee"
  setup_stale_pr_without_discussion "$pr_num"

  local HAS_DISCUSSION_LABEL
  HAS_DISCUSSION_LABEL=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels[].name' 2>/dev/null | grep -i '^discussion$' || echo "")

  if [[ -z "$HAS_DISCUSSION_LABEL" ]]; then
    print_result "PR without discussion label detected" "PASS"
  else
    print_result "PR without discussion label detected" "FAIL" "Discussion label incorrectly detected"
  fi

  local output
  if output=$(REPO="$TEST_REPO" DAYS=21 DRY_RUN=0 bash "$BOT_SCRIPT" 2>&1); then
    print_result "script executed for stale PR without discussion label" "PASS"
  else
    print_result "script executed for stale PR without discussion label" "FAIL" "Bot exited non-zero: $output"
  fi

  if [[ -f "$GH_MOCK_DIR/actions.log" ]] && grep -q "CLOSED_PR_$pr_num" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "script closed stale PR without discussion label" "PASS"
  else
    print_result "script closed stale PR without discussion label" "FAIL" "Expected CLOSED_PR_$pr_num in actions.log"
  fi

  if [[ -f "$GH_MOCK_DIR/actions.log" ]] && grep -q "UNASSIGNED_${assignee}_FROM_${issue_num}" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "script unassigned user for stale PR without discussion label" "PASS"
  else
    print_result "script unassigned user for stale PR without discussion label" "FAIL" "Expected UNASSIGNED_${assignee}_FROM_${issue_num} in actions.log"
  fi
}

# Test 3: Verify label check uses jq filter correctly
test_jq_filter_correctness() {
  echo ""
  echo "Test 3: Mock correctly executes jq filters"
  echo "=================================================================="

  setup_pr_with_discussion_label "300"
  local result
  result=$(gh pr view "300" --repo "$TEST_REPO" --json labels --jq '.labels[].name' 2>/dev/null || echo "")

  if echo "$result" | grep -q "discussion"; then
    print_result "Mock executes .labels[].name filter" "PASS"
  else
    print_result "Mock executes .labels[].name filter" "FAIL" "Expected 'discussion' in output, got '$result'"
  fi

  # Test with no discussion label using same filter
  setup_stale_pr_without_discussion "301"
  result=$(gh pr view "301" --repo "$TEST_REPO" --json labels --jq '.labels[].name' 2>/dev/null || echo "")

  if ! echo "$result" | grep -qi "^discussion$"; then
    print_result "Mock handles .labels[].name without discussion" "PASS"
  else
    print_result "Mock handles .labels[].name without discussion" "FAIL" "Unexpected discussion label in '$result'"
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
  COMMITS_JSON=$(gh api "repos/$TEST_REPO/pulls/$pr_num/commits" --paginate 2>/dev/null || echo "[]")

  if echo "$COMMITS_JSON" | jq -e 'length > 0' >/dev/null 2>&1; then
    print_result "Active PR has commit data" "PASS"

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

# Test 6: Verify mock handles varying jq expressions
test_log_output() {
  echo ""
  echo "Test 6: Mock handles varying jq filter expressions"
  echo "==================================================="

  setup_pr_with_discussion_label "600"

  local pr_num="600"
  local output
  output=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '[.labels[] | select(.name == "discussion") | .name]' 2>/dev/null || echo "[]")

  if echo "$output" | grep -q "discussion"; then
    print_result "Mock executes complex jq with select and map" "PASS"
  else
    print_result "Mock executes complex jq with select and map" "FAIL" "Expected 'discussion' in output"
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
{"labels":[{"name":"bug"},{"name":"discussion"},{"name":"CICD"}]}
EOF

  local pr_num="700"
  local label_count
  label_count=$(gh pr view "$pr_num" --repo "$TEST_REPO" --json labels --jq '.labels | length' 2>/dev/null || echo "0")

  if [[ "$label_count" == "3" ]]; then
    print_result "Mock executes .labels | length filter" "PASS"
  else
    print_result "Mock executes .labels | length filter" "FAIL" "Expected 3 labels, got '$label_count'"
  fi
}

# Test 8: Case-insensitive discussion label handling
test_case_insensitivity() {
  echo ""
  echo "Test 8: Label matching is case-insensitive"
  echo "==========================================="

  local issue_num="8000"
  local pr_num="800"
  local assignee="bob"

  setup_labeled_pr_with_linked_issue "$issue_num" "$pr_num" "$assignee" "Discussion"

  local output
  if output=$(REPO="$TEST_REPO" DAYS=21 DRY_RUN=0 bash "$BOT_SCRIPT" 2>&1); then
    print_result "script executed for case-insensitive label" "PASS"
  else
    print_result "script executed for case-insensitive label" "FAIL" "Bot exited non-zero: $output"
  fi

  if grep -Eq "\\[SKIP\\].*discussion" <<<"$output"; then
    print_result "case-insensitive discussion skip log emitted" "PASS"
  else
    print_result "case-insensitive discussion skip log emitted" "FAIL" "Expected discussion-label skip log"
  fi

  if [[ ! -f "$GH_MOCK_DIR/actions.log" ]] || ! grep -q "CLOSED_PR_$pr_num" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "bot did NOT close PR with 'Discussion' label" "PASS"
  else
    print_result "bot did NOT close PR with 'Discussion' label" "FAIL" "PR was incorrectly closed"
  fi

  if [[ ! -f "$GH_MOCK_DIR/actions.log" ]] || ! grep -q "UNASSIGNED_${assignee}_FROM_${issue_num}" "$GH_MOCK_DIR/actions.log" 2>/dev/null; then
    print_result "bot did NOT unassign issue for 'Discussion' label" "PASS"
  else
    print_result "bot did NOT unassign issue for 'Discussion' label" "FAIL" "Assignee was incorrectly removed"
  fi
}

main() {
  echo "=============================================="
  echo "  Bot Inactivity Unassign - Test Suite"
  echo "=============================================="
  echo ""

  setup
  trap cleanup EXIT

  create_gh_mock

  rm -f "$GH_MOCK_DIR/actions.log"

  test_pr_with_discussion_label_not_closed
  test_stale_pr_without_discussion_closed
  test_jq_filter_correctness
  test_closed_pr_skipped
  test_active_pr_not_closed
  test_log_output
  test_multiple_labels_with_discussion
  test_case_insensitivity

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

main "$@"
