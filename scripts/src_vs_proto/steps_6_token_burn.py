#!/usr/bin/env python3
"""
Step 6: Compare token transaction SDK classes (Step 3) with proto attributes (Step 4)
         for multiple token transactions
         + regex + mapping to check if proto really missing
         + logging missing proto mappings
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
    "tokens": "token_ids",
    "serialNumbers": "serials",
    "account": "account_id",
    "set_account": "set_account_id"
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

# Mapping of Step 3 module names -> SDK class names
SDK_MODULE_CLASS_MAP = {
    "token_burn_transaction": "TokenBurnTransaction",
    "token_associate_transaction": "TokenAssociateTransaction",
    "token_dissociate_transaction": "TokenDissociateTransaction",
    "token_mint_transaction": "TokenMintTransaction",
}

# Mapping of SDK class -> proto class
TRANSACTION_PROTO_MAP = {
    "TokenBurnTransaction": "TokenBurnTransactionBody",
    "TokenAssociateTransaction": "TokenAssociateTransactionBody",
    "TokenDissociateTransaction": "TokenDissociateTransactionBody",
    "TokenMintTransaction": "TokenMintTransactionBody",
}

if __name__ == "__main__":
    # Load Step 3 (SDK classes)
    step3_module = load_module(STEP3_FILE, "step3_token_classes")
    # Load Step 4 (proto mappings)
    step4_module = load_module(STEP4_FILE, "step4_proto_attributes")
    proto_mappings = getattr(step4_module, "proto_mappings", {})

    print("\n📦 All proto mappings available in Step 4:")
    for k in sorted(proto_mappings.keys()):
        print(" -", k)

    for sdk_module_name, sdk_class_name in SDK_MODULE_CLASS_MAP.items():
        # Get SDK info
        sdk_module = getattr(step3_module, sdk_module_name, None)
        sdk_class_info = getattr(sdk_module, sdk_class_name, None) if sdk_module else {'attributes': [], 'setters': []}

        # Get proto info
        proto_class_name = TRANSACTION_PROTO_MAP.get(sdk_class_name, "")
        proto_info = proto_mappings.get(proto_class_name)

        if proto_info is None:
            print(f"\n⚠️ Proto mapping missing for {proto_class_name} (SDK {sdk_class_name})")
            proto_info = {'attributes': [], 'setters': []}

        # Map proto attributes and setters to SDK equivalents
        mapped_proto_attrs = [map_proto_to_sdk(a) for a in proto_info['attributes']]
        mapped_proto_setters = [map_proto_setter_to_sdk(s) for s in proto_info['setters']]

        # Compute missing attributes and setters
        missing_attributes = [a for a in mapped_proto_attrs if a not in sdk_class_info['attributes']]
        missing_setters = [s for s in mapped_proto_setters if s not in sdk_class_info['setters']]

        print(f"\n💠 {sdk_class_name} vs {proto_class_name}")
        print("✅ SDK Attributes:", sdk_class_info['attributes'])
        print("✅ SDK Setters:", sdk_class_info['setters'])
        print("📦 Proto Attributes (mapped):", mapped_proto_attrs)
        print("📦 Proto Setters (mapped):", mapped_proto_setters)

        if missing_attributes or missing_setters:
            print("⚠️ Missing in SDK:")
            if missing_attributes:
                print(" - Attributes:", missing_attributes)
            if missing_setters:
                print(" - Setters:", missing_setters)
        else:
            print("✅ No proto attributes or setters are actually missing in SDK")
