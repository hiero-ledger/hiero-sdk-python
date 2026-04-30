#!/usr/bin/env bash
set -euo pipefail

# Test suite for cron-calls dynamic time computation
# Validates the shared compute-time-until-meeting.py helper used in
# cron-calls-community.sh and cron-calls-office-hours.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/compute-time-until-meeting.py"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

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

# Test 1: Standard case — 4 hours before meeting
test_standard_4_hours() {
  echo ""
  echo "Test 1: Standard case — 4 hours before meeting (10:00 → 14:00)"
  echo "================================================================"

  local result
  result=$(python3 "$HELPER" 14 "10:00")

  if [[ "$result" == "4 hours" ]]; then
    print_result "4 hours before meeting" "PASS"
  else
    print_result "4 hours before meeting" "FAIL" "Expected '4 hours', got '$result'"
  fi
}

# Test 2: Delayed run — 3 hours and 7 minutes remaining
test_delayed_run() {
  echo ""
  echo "Test 2: Delayed run — 3 hours 7 minutes remaining (10:53 → 14:00)"
  echo "==================================================================="

  local result
  result=$(python3 "$HELPER" 14 "10:53")

  if [[ "$result" == "3 hours and 7 minutes" ]]; then
    print_result "Delayed run shows 3 hours and 7 minutes" "PASS"
  else
    print_result "Delayed run shows 3 hours and 7 minutes" "FAIL" "Expected '3 hours and 7 minutes', got '$result'"
  fi
}

# Test 3: Just minutes remaining
test_just_minutes() {
  echo ""
  echo "Test 3: Just minutes remaining (13:45 → 14:00)"
  echo "================================================"

  local result
  result=$(python3 "$HELPER" 14 "13:45")

  if [[ "$result" == "15 minutes" ]]; then
    print_result "15 minutes remaining" "PASS"
  else
    print_result "15 minutes remaining" "FAIL" "Expected '15 minutes', got '$result'"
  fi
}

# Test 4: Exact whole hours
test_exact_hours() {
  echo ""
  echo "Test 4: Exact whole hours (12:00 → 14:00)"
  echo "==========================================="

  local result
  result=$(python3 "$HELPER" 14 "12:00")

  if [[ "$result" == "2 hours" ]]; then
    print_result "Exactly 2 hours remaining" "PASS"
  else
    print_result "Exactly 2 hours remaining" "FAIL" "Expected '2 hours', got '$result'"
  fi
}

# Test 5: Already past meeting time — clamped to 0
test_past_meeting_time() {
  echo ""
  echo "Test 5: Already past meeting time (15:00 → 14:00)"
  echo "==================================================="

  local result
  result=$(python3 "$HELPER" 14 "15:00")

  if [[ "$result" == "0 minutes" ]]; then
    print_result "Past meeting time shows 0 minutes" "PASS"
  else
    print_result "Past meeting time shows 0 minutes" "FAIL" "Expected '0 minutes', got '$result'"
  fi
}

# Test 6: Singular hour — 1 hour remaining
test_singular_hour() {
  echo ""
  echo "Test 6: Singular hour (13:00 → 14:00)"
  echo "======================================="

  local result
  result=$(python3 "$HELPER" 14 "13:00")

  if [[ "$result" == "1 hour" ]]; then
    print_result "Singular hour formatting" "PASS"
  else
    print_result "Singular hour formatting" "FAIL" "Expected '1 hour', got '$result'"
  fi
}

# Test 7: Singular minute — 1 hour and 1 minute
test_singular_minute() {
  echo ""
  echo "Test 7: Singular minute (12:59 → 14:00)"
  echo "========================================="

  local result
  result=$(python3 "$HELPER" 14 "12:59")

  if [[ "$result" == "1 hour and 1 minute" ]]; then
    print_result "Singular hour and minute formatting" "PASS"
  else
    print_result "Singular hour and minute formatting" "FAIL" "Expected '1 hour and 1 minute', got '$result'"
  fi
}

# Test 8: Different meeting hour
test_different_meeting_hour() {
  echo ""
  echo "Test 8: Different meeting hour (08:30 → 12:00)"
  echo "================================================"

  local result
  result=$(python3 "$HELPER" 12 "08:30")

  if [[ "$result" == "3 hours and 30 minutes" ]]; then
    print_result "Different meeting hour works" "PASS"
  else
    print_result "Different meeting hour works" "FAIL" "Expected '3 hours and 30 minutes', got '$result'"
  fi
}

# Test 9: Rounding with seconds — ceil rounds partial minutes up
test_rounding_with_seconds() {
  echo ""
  echo "Test 9: Rounding with seconds (10:53:30 → 14:00) rounds up"
  echo "============================================================"

  local result
  result=$(python3 "$HELPER" 14 "10:53:30")

  if [[ "$result" == "3 hours and 7 minutes" ]]; then
    print_result "Partial minute rounds up correctly" "PASS"
  else
    print_result "Partial minute rounds up correctly" "FAIL" "Expected '3 hours and 7 minutes', got '$result'"
  fi
}

# Test 10: Seconds just past the minute boundary
test_seconds_just_past_boundary() {
  echo ""
  echo "Test 10: Seconds just past boundary (13:00:01 → 14:00) rounds up to 60 min"
  echo "============================================================================"

  local result
  result=$(python3 "$HELPER" 14 "13:00:01")

  if [[ "$result" == "1 hour" ]]; then
    print_result "Just past boundary rounds up to full hour" "PASS"
  else
    print_result "Just past boundary rounds up to full hour" "FAIL" "Expected '1 hour', got '$result'"
  fi
}

main() {
  echo "=============================================="
  echo "  Cron Calls Time Computation - Test Suite"
  echo "=============================================="

  if [[ ! -f "$HELPER" ]]; then
    echo -e "${RED}ERROR: Helper script not found at $HELPER${NC}"
    exit 1
  fi

  test_standard_4_hours
  test_delayed_run
  test_just_minutes
  test_exact_hours
  test_past_meeting_time
  test_singular_hour
  test_singular_minute
  test_different_meeting_hour
  test_rounding_with_seconds
  test_seconds_just_past_boundary

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
