import os
from collections import defaultdict

EXCLUDE_DIRS = ['hapi', '__pycache__']


# -----------------------------
# Token-based normalization
# -----------------------------
def tokenize_filename(path):
    """Split a filename (without extension) into tokens."""
    filename = os.path.splitext(os.path.basename(path))[0]
    return filename.split("_")


def longest_shared_prefix_tokens(a, b):
    """Return longest shared prefix between two token lists."""
    prefix = []
    for x, y in zip(a, b):
        if x == y:
            prefix.append(x)
        else:
            break
    return prefix


def normalize_example_against_src(example_path, src_token_map, folder):
    """
    Determine normalized name for an example file by comparing it to all
    src files in the *same folder* and using the longest shared prefix.
    """
    ex_tokens = tokenize_filename(example_path)

    best_prefix = []
    src_tokens_for_folder = src_token_map.get(folder, [])

    for src_tokens in src_tokens_for_folder:
        shared = longest_shared_prefix_tokens(ex_tokens, src_tokens)
        if len(shared) > len(best_prefix):
            best_prefix = shared

    # use longest shared prefix
    if best_prefix:
        return "_".join(best_prefix)

    # fallback: two tokens
    return "_".join(ex_tokens[:2])


# -----------------------------
# File helpers
# -----------------------------
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


# -----------------------------
# Matching helpers
# -----------------------------
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


# -----------------------------
# Main function
# -----------------------------
def match_examples_to_src(examples_path, src_path):
    examples_files = list_files(examples_path, EXCLUDE_DIRS)
    src_files = list_files(src_path, EXCLUDE_DIRS)

    # Build token maps for SRC files
    src_token_map = defaultdict(list)  # folder -> list of token lists
    for f in src_files:
        folder = get_folder(f)
        tokens = tokenize_filename(f)
        src_token_map[folder].append(tokens)

    # Now build a normalized mapping for src files
    src_map = defaultdict(list)
    for f in src_files:
        folder = get_folder(f)
        norm = "_".join(tokenize_filename(f))  # raw tokens joined
        src_map[(folder, norm)].append(f)

    matched = defaultdict(list)
    unmatched_examples = []
    unmatched_src_set = set(src_files)

    for ex in examples_files:
        folder_ex = get_folder(ex)

        # Normalize example using longest shared prefix with src files
        norm_ex = normalize_example_against_src(ex, src_token_map, folder_ex)

        # Now match using full map
        matched_files = match_exact_folder(norm_ex, folder_ex, src_map, unmatched_src_set)
        if not matched_files:
            matched_files = match_by_filename_only(norm_ex, src_map, unmatched_src_set)

        if matched_files:
            for src_file in matched_files:
                matched[src_file].append(ex)
        else:
            unmatched_examples.append(ex)

    print_results(matched, unmatched_examples, unmatched_src_set, examples_path, src_path)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    examples_path = os.path.abspath("./examples")
    src_path = os.path.abspath("./src/hiero_sdk_python")
    match_examples_to_src(examples_path, src_path)
