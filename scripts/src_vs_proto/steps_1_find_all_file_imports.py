# scripts/extract_token_classes_with_paths.py
"""
Scans the hiero_sdk_python tokens source directory and extracts
all top-level classes in each Python file. Generates a Python file
with explicit imports for each class from its file.

Example output:

from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.custom_fee import CustomFee
...
"""

import ast
from pathlib import Path

# Paths (adjust if needed)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_DIR = PROJECT_ROOT / "src" / "hiero_sdk_python" / "tokens"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "src_vs_proto"
OUTPUT_FILE = OUTPUT_DIR / "steps_1_extracted_token_classes_with_paths.py"

def extract_classes_from_file(file_path: Path):
    """Return a list of top-level class names defined in a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    imports = []

    for py_file in TOKENS_DIR.glob("*.py"):
        classes = extract_classes_from_file(py_file)
        if not classes:
            continue
        module_name = py_file.stem  # file name without .py
        for cls in classes:
            import_line = f"from hiero_sdk_python.tokens.{module_name} import {cls}"
            imports.append(import_line)
            print(f"Found class {cls} in {module_name}.py")

    # Write the output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated imports for token classes\n\n")
        for line in sorted(imports):
            f.write(f"{line}\n")

    print(f"\nAll token classes with proper paths written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
