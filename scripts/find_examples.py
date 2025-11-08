"""
Run:
uv run scripts/find_examples.py

scripts/generate_example_imports.py

Automatically scans the `examples/` directory and generates
a Python snippet with imports and a list of example modules to run.
"""

import os
from pathlib import Path

# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

# Files to skip
SKIPPED_FILES = {
    "__init__.py",
    "node_create.py",
    "node_delete.py",
    "node_update.py",
}

# Output file
OUTPUT_FILE = Path(__file__).parent / "example_modules.py"

def main():
    modules = []
    import_lines = []

    for file in sorted(EXAMPLES_DIR.glob("*.py")):
        if file.name in SKIPPED_FILES:
            continue
        module_name = file.stem
        import_line = f"import examples.{module_name} as {module_name}"
        import_lines.append(import_line)
        modules.append(module_name)

    # Generate Python code
    code = "# Auto-generated module imports for run_examples.py\n\n"
    code += "\n".join(import_lines)
    code += "\n\nEXAMPLES_TO_RUN = [\n"
    for m in modules:
        code += f"    {m},\n"
    code += "]\n\nSKIPPED_EXAMPLES = " + str(list(SKIPPED_FILES)) + "\n"
    code += 'LOG_MODE = "all"\n'

    # Write to output file
    with open(OUTPUT_FILE, "w") as f:
        f.write(code)

    print(f"Generated example modules list in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
