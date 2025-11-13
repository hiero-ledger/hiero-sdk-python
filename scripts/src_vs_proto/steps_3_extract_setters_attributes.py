# scripts/extract_token_classes_info_readable.py
"""
Step 3: Extract all token classes, their attributes, and setter methods.
Generates a Python file with:
1. Imports for each token module (for Pylance/IDE)
2. Class info: attributes and setter methods listed line by line
3. Error log for failed parsing
"""

import ast
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_DIR = PROJECT_ROOT / "src" / "hiero_sdk_python" / "tokens"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "src_vs_proto"
OUTPUT_FILE = OUTPUT_DIR / "steps_3_token_classes_info_readable.py"
ERROR_FILE = OUTPUT_DIR / "steps_3_token_classes_errors.log"

def extract_classes_from_file(file_path: Path, error_log: list):
    """Return top-level classes with attributes and setters from a Python file."""
    classes_info = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as e:
        error_log.append(f"{file_path}: Failed to parse ({e})")
        return classes_info

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls_name = node.name
            init_attrs = []
            setters = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name == "__init__":
                        init_attrs = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    if item.name.startswith("set_"):
                        setters.append(item.name)
            classes_info[cls_name] = {"attributes": init_attrs, "setters": setters}
    return classes_info

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_classes_info = {}
    error_log = []
    modules_seen = set()

    for py_file in TOKENS_DIR.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        module_name = py_file.stem
        modules_seen.add(module_name)
        class_info = extract_classes_from_file(py_file, error_log)
        if class_info:
            all_classes_info.update({f"{module_name}.{k}": v for k, v in class_info.items()})
        else:
            error_log.append(f"{py_file}: No classes found or all failed parsing.")

    # Write class info with imports
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated class info: imports, attributes and setters\n\n")
        # Write imports for all modules
        for mod in sorted(modules_seen):
            f.write(f"from hiero_sdk_python.tokens import {mod}\n")
        f.write("\n")

        # Write classes info in human-readable format
        for full_cls_name, info in sorted(all_classes_info.items()):
            file_name = full_cls_name.split(".")[0] + ".py"
            f.write(f"# File: {file_name}\n")
            f.write(f"{full_cls_name} = {{\n")
            f.write("    'attributes': [\n")
            for attr in info['attributes']:
                f.write(f"        '{attr}',\n")
            f.write("    ],\n")
            f.write("    'setters': [\n")
            for setter in info['setters']:
                f.write(f"        '{setter}',\n")
            f.write("    ]\n")
            f.write("}\n\n")

    # Write error log
    with open(ERROR_FILE, "w", encoding="utf-8") as f:
        if error_log:
            f.write("# Errors encountered during parsing\n\n")
            for err in error_log:
                f.write(err + "\n")
        else:
            f.write("# No errors encountered\n")

    print(f"Class info written to: {OUTPUT_FILE}")
    print(f"Errors (if any) written to: {ERROR_FILE}")

if __name__ == "__main__":
    main()
