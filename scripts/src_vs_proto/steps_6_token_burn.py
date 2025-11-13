#!/usr/bin/env python3
"""
Step 6: Extract TokenBurnTransaction info from Step 3 output
         + corresponding proto attributes and setters from Step 4 output
         + regex + mapping to check if proto really missing
"""

from pathlib import Path
import importlib.util
import sys
import re

# Step 3 and Step 4 generated files
STEP3_FILE = Path(__file__).resolve().parent / "steps_3_token_classes_info_readable.py"
STEP4_FILE = Path(__file__).resolve().parent / "steps_4_token_classes_proto_attributes.py"

def load_module(file_path: Path, module_name: str):
    """Dynamically load a Python file as a module."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def camel_to_snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

# Special proto -> SDK mappings
PROTO_TO_SDK_MAP = {
    "token": "token_id",
    "serialNumbers": "serials",
}

def map_proto_to_sdk(proto_attr: str) -> str:
    """Apply special mapping rules + snake_case conversion."""
    if proto_attr in PROTO_TO_SDK_MAP:
        return PROTO_TO_SDK_MAP[proto_attr]
    return camel_to_snake(proto_attr)

def map_proto_setter_to_sdk(proto_setter: str) -> str:
    """Convert proto setter to SDK setter."""
    if proto_setter.startswith("set_"):
        core = proto_setter[4:]  # remove 'set_'
        return f"set_{map_proto_to_sdk(core)}"
    return proto_setter

if __name__ == "__main__":
    # Load Step 3 (SDK classes)
    step3_module = load_module(STEP3_FILE, "step3_token_classes")
    tb_info = getattr(step3_module.token_burn_transaction, "TokenBurnTransaction", None)
    if not tb_info:
        tb_info = {'attributes': [], 'setters': []}

    # Load Step 4 (proto mappings)
    step4_module = load_module(STEP4_FILE, "step4_proto_attributes")
    proto_info = getattr(step4_module, "proto_mappings", {}).get("TokenBurnTransactionBody", None)
    if not proto_info:
        proto_info = {'attributes': [], 'setters': []}

    # Map proto attributes and setters to SDK equivalents
    mapped_proto_attrs = [map_proto_to_sdk(a) for a in proto_info['attributes']]
    mapped_proto_setters = [map_proto_setter_to_sdk(s) for s in proto_info['setters']]

    # Compute missing attributes and setters
    missing_attributes = [a for a in mapped_proto_attrs if a not in tb_info['attributes']]
    missing_setters = [s for s in mapped_proto_setters if s not in tb_info['setters']]

    print("✅ SDK Attributes:", tb_info['attributes'])
    print("✅ SDK Setters:", tb_info['setters'])
    print("\n✅ Proto Attributes (mapped):", mapped_proto_attrs)
    print("✅ Proto Setters (mapped):", mapped_proto_setters)

    if missing_attributes or missing_setters:
        print("\n⚠️ Proto attributes/setters really missing in SDK TokenBurnTransaction:")
        if missing_attributes:
            print("⚠️Missing attributes:", missing_attributes)
        if missing_setters:
            print("⚠️Missing setters:", missing_setters)
    else:
        print("\n✅ No proto attributes or setters are actually missing in the SDK TokenBurnTransaction")
