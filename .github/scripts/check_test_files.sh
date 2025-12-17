#!/usr/bin/env bash
RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

# Base directories where test files should reside
TEST_DIRS=("tests/unit" "tests/integration")
EXCEPTION_NAMES=("conftest.py" "init.py" "__init__.py" "mock_server.py")
DIFF_FILES=$(git diff --name-status origin/main)
ERRORS=()

function is_in_test_dir() {
    local file="$1"
    for dir in "${TEST_DIRS[@]}"; do
        case "$file" in
            "$dir"*)
                return 0
                ;;
        esac
    done
    return 1
}

function check_test_file_name() {
  local filename="$1"
  if is_in_test_dir "$filename"; then
    for exception in "${EXCEPTION_NAMES[@]}"; do
      if [[ $(basename "$filename") == "$exception" ]]; then
        return 0
      fi
    done
    if [[ $(basename "$filename") != *_test.py ]]; then
      ERRORS+=("${RED}ERROR${RESET}: Test file '$filename' doesn't end with '_test'. ${YELLOW}It has to follow the pytest naming convention.")
      return 1
    fi
  fi
  return 0
}

while IFS=$'\t' read -r status file1 file2; do
  case "$status" in
    A) check_test_file_name "$file1" ;;
    R*) check_test_file_name "$file2" ;;
    C*) check_test_file_name "$file2" ;;
  esac
done <<< "$DIFF_FILES"

if (( ${#ERRORS[@]} > 0 )); then
  for err in "${ERRORS[@]}"; do
    echo -e "$err"
  done
  exit 1
fi
