import os

def list_files(base_dir, ignore_names=None):
    """List all files in a directory recursively, ignoring specified names."""
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return []

    ignore_names = ignore_names or []
    file_list = []

    for root, dirs, files in os.walk(base_dir):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_names]

        for file in files:
            # Skip ignored filenames
            if file in ignore_names:
                continue
            rel_path = os.path.relpath(os.path.join(root, file), base_dir)
            file_list.append(rel_path)

    return file_list


def main():
    # repo_root is the parent directory of scripts/
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    examples_dir = os.path.join(repo_root, "examples")
    sdk_dir = os.path.join(repo_root, "src", "hiero_sdk_python")

    ignore_list = ["hapi", "__pycache__"]

    # List examples
    print("📁 Files in examples/:")
    examples_files = list_files(examples_dir, ignore_names=ignore_list)
    for f in examples_files:
        print(" -", f)

    # List SDK files
    print("\n📁 Files in src/hiero_sdk_python/ (ignoring 'hapi' and '__pycache__'):")
    sdk_files = list_files(sdk_dir, ignore_names=ignore_list)
    for f in sdk_files:
        print(" -", f)


if __name__ == "__main__":
    main()
