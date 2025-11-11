import os
import re
from collections import defaultdict

EXCLUDE_DIRS = ['hapi', '__pycache__']

def normalize_filename(path):
    filename = os.path.splitext(os.path.basename(path))[0]
    # Strip common suffix patterns after the base operation
    filename = re.sub(
        r'(_(ed25519|ecdsa|der|hbar|nft|fungible|auto|signature_required|finite|infinite|no_constructor_parameters|with_bytecode|with_constructor_parameters|non_fungible|key|nfts|fungible_token|revenue_generating|with_value|_to_bytes))+$',
        '',
        filename
    )
    return filename



# Get folder path without filename
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

        # Try exact folder match first
        key = (folder_ex, norm_ex)
        if key in src_map:
            for src_file in src_map[key]:
                matched[src_file].append(ex)
                unmatched_src_set.discard(src_file)
        else:
            # Try matching by filename only if folder doesn't match
            found = False
            for (src_folder, src_norm), src_list in src_map.items():
                if src_norm == norm_ex:
                    for src_file in src_list:
                        matched[src_file].append(ex)
                        unmatched_src_set.discard(src_file)
                    found = True
                    break
            if not found:
                unmatched_examples.append(ex)
    # Print matches
    print("=== Matched files ===")
    for src_file, ex_list in matched.items():
        for ex in ex_list:
            # Print relative paths instead of full absolute paths
            print(f"{os.path.relpath(examples_path)}/{ex} <-> {src_file}")

    print("\n=== Unmatched example files ===")
    for ex in sorted(unmatched_examples):
        print(f"{os.path.relpath(examples_path)}/{ex}")

    print("\n=== Unmatched src files ===")
    for src in sorted(unmatched_src_set):
        # Just show the path relative to src_path
        print(f"{os.path.relpath(src_path)}/{src}")

if __name__ == "__main__":
    examples_path = os.path.abspath("./examples")
    src_path = os.path.abspath("./src/hiero_sdk_python")
    match_examples_to_src(examples_path, src_path)