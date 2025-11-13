"""
Step 5: Build a mapping between token source classes and proto classes.

✅ Generates:
- Full imports for Pylance (no missing references)
- Clean TRANSACTIONS dict mapping token classes → proto classes

Output: steps_5_proto_to_src.py
"""

import sys
from pathlib import Path
from collections import defaultdict

# Paths
STEP1_FILE = Path(__file__).parent / "steps_1_extracted_token_classes_with_paths.py"
STEP2_FILE = Path(__file__).parent / "steps_2_extracted_token_proto_imports.py"
OUTPUT_FILE = Path(__file__).parent / "steps_5_proto_to_src.py"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def load_imports(filepath: Path):
    """Return {class_name: module_name} from step 1."""
    classes = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("from hiero_sdk_python.tokens."):
                # from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
                parts = line.split()
                module = parts[1].replace("hiero_sdk_python.tokens.", "")
                cls = parts[-1]
                classes[cls] = module
    return classes


def load_proto_imports(filepath: Path):
    """Return {token_module: proto_path} from step 2."""
    protos = {}
    current_module = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") and line.endswith(".py"):
                current_module = line.replace("#", "").replace(".py", "").strip()
            elif line.startswith("import ") and current_module:
                proto_path = line.replace("import ", "").strip()
                protos[current_module] = proto_path
    return protos


def build_mapping(classes, protos):
    """Build the mapping of class → proto reference."""
    mapping = {}
    proto_imports = set()
    token_imports = set()
    matched, unmatched = [], []

    for cls, module in sorted(classes.items()):
        token_imports.add(module)
        proto_path = protos.get(module)
        if not proto_path:
            mapping[cls] = {"cls": f"{module}.{cls}", "proto_cls": None}
            unmatched.append(cls)
            continue

        parts = proto_path.split(".")
        # Handle both cases: *_pb2 or *_pb2.ClassName
        if len(parts) > 1 and parts[-1][0].isupper():
            proto_mod = ".".join(parts[:-1])
            proto_cls = parts[-1]
            proto_ref = f"{proto_mod.split('.')[-1]}.{proto_cls}"
            proto_imports.add(proto_mod)
        else:
            proto_mod = proto_path
            proto_ref = proto_mod.split(".")[-1]
            proto_imports.add(proto_mod)

        mapping[cls] = {
            "cls": f"{module}.{cls}",
            "proto_cls": proto_ref,
        }
        matched.append(cls)

    return mapping, token_imports, proto_imports, matched, unmatched


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    classes = load_imports(STEP1_FILE)
    protos = load_proto_imports(STEP2_FILE)
    mapping, token_imports, proto_imports, matched, unmatched = build_mapping(classes, protos)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated: mapping of src token classes to proto classes\n")
        f.write("# This file includes imports for IDE/Pylance support.\n\n")

        # Token module imports
        for mod in sorted(token_imports):
            f.write(f"from hiero_sdk_python.tokens import {mod}\n")
        f.write("\n")

        # Proto imports
        for proto in sorted(proto_imports):
            short = proto.split(".")[-1]
            f.write(f"from hiero_sdk_python.hapi.services import {short}\n")
        f.write("\n")

        f.write("TRANSACTIONS = {\n")
        for cls, data in sorted(mapping.items()):
            proto_str = "None" if not data["proto_cls"] else data["proto_cls"]
            f.write(
                f"    '{cls}': {{'cls': {data['cls']}, 'proto_cls': {proto_str}}},\n"
            )
        f.write("}\n")

    print(f"\n✅ Mapping written to: {OUTPUT_FILE}")
    print(f"Total token classes: {len(classes)}")
    print(f"Matched: {len(matched)}")
    print(f"Unmatched: {len(unmatched)}")

    if unmatched:
        print("\n⚠️ Unmatched classes:")
        for name in unmatched:
            print(f"  - {name}")


if __name__ == "__main__":
    main()

