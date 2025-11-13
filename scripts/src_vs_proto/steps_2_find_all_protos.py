# scripts/extract_token_proto_imports.py
"""
Scans the hiero_sdk_python tokens source directory, parses each Python file,
and extracts all proto modules that are imported in each file.

Output is written to a file with the imports grouped by token module.
"""

import ast
from pathlib import Path

# Paths (adjust if needed)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_DIR = PROJECT_ROOT / "src" / "hiero_sdk_python" / "tokens"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "src_vs_proto"
OUTPUT_FILE = OUTPUT_DIR / "steps_2_extracted_token_proto_imports.py"

def extract_proto_imports(file_path: Path):
    """Return a list of proto modules imported in a Python file."""
    proto_imports = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # Filter only imports from hiero_sdk_python.hapi.services
            if module.startswith("hiero_sdk_python.hapi.services"):
                for alias in node.names:
                    proto_imports.append(f"{module}.{alias.name}")
    return proto_imports

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_proto_imports = {}

    for py_file in TOKENS_DIR.glob("*.py"):
        token_module = py_file.stem
        proto_imports = extract_proto_imports(py_file)
        if proto_imports:
            all_proto_imports[token_module] = proto_imports
            print(f"Found proto imports in {token_module}: {proto_imports}")

    # Write output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated proto imports per token module\n\n")
        for module, imports in sorted(all_proto_imports.items()):
            f.write(f"# {module}.py\n")
            for imp in imports:
                f.write(f"import {imp}\n")
            f.write("\n")

    print(f"\nAll proto imports written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
