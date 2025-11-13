"""
Step 4: Extract attributes and setters from proto classes referenced by token modules.
This version generates a flat mapping proto_mappings[class_name] -> {attributes, setters}.
"""

import importlib
from pathlib import Path

STEP2_OUTPUT = Path(__file__).parent / "steps_2_extracted_token_proto_imports.py"
OUTPUT_FILE = Path(__file__).parent / "steps_4_token_classes_proto_attributes.py"
ERROR_FILE = Path(__file__).parent / "steps_4_token_classes_proto_errors.log"


def parse_step2_imports():
    """
    Parse Step 2 output and return a mapping of token_file -> list of proto imports.
    Each proto import is (full_import_path, class_name_or_none)
    """
    token_proto_map = {}
    current_token_file = None

    with open(STEP2_OUTPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                if line.startswith("#") and line.endswith(".py"):
                    current_token_file = line[2:].strip()
                    token_proto_map[current_token_file] = []
            elif line.startswith("import") and current_token_file:
                full_import = line.split()[1]
                parts = full_import.split(".")
                proto_class = parts[-1] if parts[-1][0].isupper() else None
                proto_module = ".".join(parts[:-1]) if proto_class else full_import
                token_proto_map[current_token_file].append((proto_module, proto_class))
    return token_proto_map


def get_proto_fields(proto_module_name, proto_class_name):
    """Dynamically import proto class and return field names and setters."""
    try:
        mod = importlib.import_module(proto_module_name)
        proto_cls = getattr(mod, proto_class_name)
        attributes = [f.name for f in proto_cls.DESCRIPTOR.fields]
        setters = [f"set_{f.name}" for f in proto_cls.DESCRIPTOR.fields]
        return attributes, setters, None
    except Exception as e:
        return [], [], str(e)


def main():
    token_proto_map = parse_step2_imports()
    error_log = []
    proto_mappings = {}

    for token_file, proto_entries in token_proto_map.items():
        for proto_module, proto_class in proto_entries:
            if not proto_class:
                continue
            attrs, setters, err = get_proto_fields(proto_module, proto_class)
            if err:
                error_log.append(f"{proto_module}.{proto_class}: {err}")
            proto_mappings[proto_class] = {
                "attributes": attrs,
                "setters": setters,
            }

    # Write proto_mappings to Step 4 output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated proto attributes and setters\n\n")
        f.write("proto_mappings = {\n")
        for cls_name, data in sorted(proto_mappings.items()):
            f.write(f"    '{cls_name}': {{\n")
            f.write("        'attributes': [\n")
            for a in data['attributes']:
                f.write(f"            '{a}',\n")
            f.write("        ],\n")
            f.write("        'setters': [\n")
            for s in data['setters']:
                f.write(f"            '{s}',\n")
            f.write("        ]\n")
            f.write("    },\n")
        f.write("}\n")

    # Write errors if any
    with open(ERROR_FILE, "w", encoding="utf-8") as f:
        if error_log:
            f.write("# Errors encountered during proto extraction\n\n")
            for e in error_log:
                f.write(e + "\n")
        else:
            f.write("# No errors encountered\n")

    print(f"Output written to: {OUTPUT_FILE}")
    print(f"Errors written to: {ERROR_FILE}")


if __name__ == "__main__":
    main()
