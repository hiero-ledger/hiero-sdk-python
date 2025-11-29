"""
Scan token modules, extract all proto imports and classes.
Generates a mapping:
    token_module -> list of (proto_module, proto_class)
"""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_DIR = PROJECT_ROOT / "src/hiero_sdk_python/tokens"
OUTPUT_FILE = Path(__file__).resolve().parent / "steps_2_extracted_token_proto_imports.py"

def extract_proto_imports(file_path: Path):
    """
    Return list of tuples: (module_name, class_name_or_None)
    """
    proto_imports = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("hiero_sdk_python.hapi.services"):
                for alias in node.names:
                    proto_imports.append((module, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("hiero_sdk_python.hapi.services"):
                    proto_imports.append((alias.name, None))  # module only
    return proto_imports

def main():
    all_proto_imports = {}
    for py_file in TOKENS_DIR.glob("*.py"):
        token_module = py_file.stem
        proto_entries = extract_proto_imports(py_file)
        if proto_entries:
            all_proto_imports[token_module] = proto_entries

    # Write Python file with mapping
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated proto imports per token module\n\n")
        f.write("token_proto_map = {\n")
        for token_module, entries in sorted(all_proto_imports.items()):
            f.write(f"    '{token_module}': [\n")
            for mod, cls in entries:
                f.write(f"        ('{mod}', '{cls}'" if cls else f"        ('{mod}', None)")
                f.write("),\n")
            f.write("    ],\n")
        f.write("}\n")

    print(f"✅ All proto imports written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
