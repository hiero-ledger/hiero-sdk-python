#!/usr/bin/env bash
set -euo pipefail

# ======================================================================================================================================================
# @file: pr-check-test-files.sh
#
# @Description A CI check written in bash that enforces the '_test.py' suffix to ensure Pytest can automatically discover 
#               new or renamed test files in a Pull Request. 
# 
# @logic: 
# 1. Identifies files as (A) Added, (R) Renamed, or (C) Copied using 'git diff' to check 
#    relevant filename ($file1 for added files, $file2 for renamed/copied files). 
# 2. Validates paths against allowed test directories (unit/integration).
# 3. Excludes specific utility (ex., conftest.py, utils.py) and non-Python files.
# 4. Parses tab-separated Git output via IFS=$'\t' to ensure robust filename handling.
# 5. Routes files using case statement based on git status
#
# @types:
# - String: Used for file paths and git status codes. 
# - Array: Used for 'TEST_DIRS', 'EXCEPTION_NAMES', and accumulating errors.
#
# @Parameters:
# - None: This script does not accept CLI arguments. It derives the input from the current Git state compared against origin/main.
#  
# @Dependencies:
# - Git: (for diff)
# - Bash: (runs the script)
# - Pytest: (naming standard)
#
# @Permissions:
# - Requires Execute permissions (chmod +x) to run. Also needs Read access to the git repository to perform the diff.
#
# @Return
# - 0: All test files follow the naming standard.
# - 1: Exits with status 1 and outputs error messages in red.
#      Includes a yellow instructional block providing reason why the file failed.
# ======================================================================================================================================================

RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

# Base directories where test files should reside
TEST_DIRS=("tests/unit" "tests/integration")
EXCEPTION_NAMES=("conftest.py" "init.py" "__init__.py" "mock_server.py" "utils.py")
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
    if [[ $(basename "$filename") != *.py ]]; then
      return 0
    fi
    for exception in "${EXCEPTION_NAMES[@]}"; do
      if [[ $(basename "$filename") == "$exception" ]]; then
        return 0
      fi
    done
    if [[ $(basename "$filename") != *_test.py ]]; then
      ERRORS+=("${RED}ERROR${RESET}: Test file '$filename' doesn't end with '_test.py'. ${YELLOW}It has to follow the pytest naming convention.")
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
