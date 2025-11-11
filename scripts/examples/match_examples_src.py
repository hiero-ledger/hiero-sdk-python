import os
import re
from collections import defaultdict

EXCLUDE_DIRS = ['hapi', '__pycache__']

def normalize_filename(path):
    filename = os.path.splitext(os.path.basename(path))[0]
    # Strip common suffix patterns after the base operation
    filename = re.sub(
        r'(_(ed25519|ecdsa|der|hbar|nft|fungible|auto|signature_required|finite|infinite|'
        r'no_constructor_parameters|with_bytecode|with_constructor_parameters|non_fungible|key|'
        r'nfts|fungible_token|revenue_generating|with_value|_to_bytes))+$',
        '',
        filename
    )
    return filename

def get_folder(path):
    return os.path.dirname(path).replace("\\", "/")

def list_files(base_path, exclude_dirs=None):
    exclude_dirs = exclude_dirs or []
    all_files = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), base_path)
            all_files.append(rel_path.replace("\\", "/"))
    return all_files

# --- Helper functions for matching ---
def match_exact_folder(norm_ex, folder_ex, src_map, unmatched_src_set):
    key = (folder_ex, norm_ex)
    if key in src_map:
        for src_file in src_map[key]:
            unmatched_src_set.discard(src_file)
        return src_map[key]
    return []

def match_by_filename_only(norm_ex, src_map, unmatched_src_set):
    for (src_folder, src_norm), src_list in src_map.items():
        if src_norm == norm_ex:
            for src_file in src_list:
                unmatched_src_set.discard(src_file)
            return src_list
    return []

def print_results(matched, unmatched_examples, unmatched_src_set, examples_path, src_path):
    print("=== Matched files ===")
    for src_file, ex_list in matched.items():
        for ex in ex_list:
            print(f"{os.path.relpath(examples_path)}/{ex} <-> {os.path.relpath(src_path)}/{src_file}")

    print("\n=== Unmatched example files ===")
    for ex in sorted(unmatched_examples):
        print(f"{os.path.relpath(examples_path)}/{ex}")

    print("\n=== Unmatched src files ===")
    for src in sorted(unmatched_src_set):
        print(f"{os.path.relpath(src_path)}/{src}")

# --- Main function ---
def match_examples_to_src(examples_path, src_path):
    examples_files = list_files(examples_path, EXCLUDE_DIRS)
    src_files = list_files(src_path, EXCLUDE_DIRS)

    # Build folder-aware normalized mapping for src
    src_map = defaultdict(list)
    for f in src_files:
        norm = normalize_filename(f)
        folder = get_folder(f)
        src_map[(folder, norm)].append(f)

    matched = defaultdict(list)
    unmatched_examples = []
    unmatched_src_set = set(src_files)

    for ex in examples_files:
        norm_ex = normalize_filename(ex)
        folder_ex = get_folder(ex)

        matched_files = match_exact_folder(norm_ex, folder_ex, src_map, unmatched_src_set)
        if not matched_files:
            matched_files = match_by_filename_only(norm_ex, src_map, unmatched_src_set)

        if matched_files:
            for src_file in matched_files:
                matched[src_file].append(ex)
        else:
            unmatched_examples.append(ex)

    print_results(matched, unmatched_examples, unmatched_src_set, examples_path, src_path)

if __name__ == "__main__":
    examples_path = os.path.abspath("./examples")
    src_path = os.path.abspath("./src/hiero_sdk_python")
    match_examples_to_src(examples_path, src_path)
