#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.examples.match_examples_src import tokenize_filename, normalize_example_against_src
from collections import defaultdict

# Test the specific problematic cases
test_cases = [
    ("examples/query/account_records_query.py", "src/hiero_sdk_python/account/account_records_query.py"),
    ("examples/query/file_contents_query.py", "src/hiero_sdk_python/file/file_contents_query.py"),
    ("examples/query/file_info_query.py", "src/hiero_sdk_python/file/file_info_query.py"),
    ("examples/query/schedule_info_query.py", "src/hiero_sdk_python/schedule/schedule_info_query.py"),
]

# Create a mock src_token_map
src_token_map = defaultdict(list)
src_files = [
    "src/hiero_sdk_python/account/account_records_query.py",
    "src/hiero_sdk_python/file/file_contents_query.py", 
    "src/hiero_sdk_python/file/file_info_query.py",
    "src/hiero_sdk_python/schedule/schedule_info_query.py",
]

for f in src_files:
    folder = os.path.dirname(f).replace("\\", "/")
    tokens = tokenize_filename(f)
    src_token_map[folder].append(tokens)

print("=== Testing Improved Matching Algorithm ===")
print()

for example_path, expected_src in test_cases:
    folder = os.path.dirname(example_path).replace("\\", "/")
    normalized = normalize_example_against_src(example_path, src_token_map, folder)
    
    print(f"Example: {example_path}")
    print(f"Normalized: {normalized}")
    print(f"Expected source: {expected_src}")
    
    # Check if normalized matches the source filename
    expected_normalized = "_".join(tokenize_filename(expected_src))
    matches = normalized == expected_normalized
    print(f"Match: {'✅ YES' if matches else '❌ NO'}")
    print()

print("=== Summary ===")
print("The improved algorithm should now correctly match:")
print("1. account_records_query.py -> account/account_records_query.py")
print("2. file_contents_query.py -> file/file_contents_query.py") 
print("3. file_info_query.py -> file/file_info_query.py")
print("4. schedule_info_query.py -> schedule/schedule_info_query.py")
