## Description

Fixes #880 

Improved the precision of `scripts/examples/match_examples_src.py` to correctly identify source files that have matching examples, even when they are located in different folder structures.

## Problem

The script was incorrectly classifying the following files as missing examples:
- `src/hiero_sdk_python/account/account_records_query.py`
- `src/hiero_sdk_python/file/file_contents_query.py`
- `src/hiero_sdk_python/file/file_info_query.py`
- `src/hiero_sdk_python/schedule/schedule_info_query.py`

These files actually have corresponding examples in `examples/query/` with identical filenames, but the token-based matching algorithm was failing to match them due to the different folder structures.

## Solution

Added a fallback matching mechanism that performs exact filename matching when the token-based and partial token matching methods fail. This ensures that files with identical names are matched regardless of their directory paths.

### Changes Made

**`scripts/examples/match_examples_src.py`:**
- Added fallback logic after existing matching attempts
- Checks for exact filename match (basename) against unmatched source files
- Removes matched files from the unmatched set to prevent duplicates

**`CHANGELOG.md`:**
- Added entry under `[Unreleased] > Fixed` section

## Testing

The fix ensures that:
- `examples/query/account_records_query.py` ↔ `src/hiero_sdk_python/account/account_records_query.py`
- `examples/query/file_contents_query.py` ↔ `src/hiero_sdk_python/file/file_contents_query.py`
- `examples/query/file_info_query.py` ↔ `src/hiero_sdk_python/file/file_info_query.py`
- `examples/query/schedule_info_query.py` ↔ `src/hiero_sdk_python/schedule/schedule_info_query.py`

All four previously unmatched files are now correctly identified as having examples.

## Checklist

- [x] Code follows project style guidelines
- [x] Changes are documented in CHANGELOG.md
- [x] Commit is signed with GPG (`-S`) and DCO (`-s`)
- [x] Self-reviewed the code
- [x] No breaking changes introduced
