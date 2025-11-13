#!/usr/bin/env python3
"""
Step 6: Compare token transaction SDK classes (Step 3) with proto attributes (Step 4)
         Accurate logging: actual proto attributes, predicted setters, SDK coverage,
         and SDK-specific extra methods
"""

from pathlib import Path
import importlib.util
import sys
import re

STEP3_FILE = Path(__file__).resolve().parent / "steps_3_token_classes_info_readable.py"
STEP4_FILE = Path(__file__).resolve().parent / "steps_4_token_classes_proto_attributes.py"

def load_module(file_path: Path, module_name: str):
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

PROTO_TO_SDK_MAP = {
    "token": "token_id",
    "tokens": "token_ids",
    "serialNumbers": "serials",
    "account": "account_id",
    "set_account": "set_account_id"
}

def map_proto_to_sdk(proto_attr: str) -> str:
    return PROTO_TO_SDK_MAP.get(proto_attr, camel_to_snake(proto_attr))

def predicted_proto_setters(proto_attrs):
    """Return predicted setters from actual proto attributes"""
    return [f"set_{map_proto_to_sdk(a)}" for a in proto_attrs]

SDK_MODULE_CLASS_MAP = {
    "token_burn_transaction": "TokenBurnTransaction",
    "token_associate_transaction": "TokenAssociateTransaction",
    "token_dissociate_transaction": "TokenDissociateTransaction",
    "token_mint_transaction": "TokenMintTransaction",
}

TRANSACTION_PROTO_MAP = {
    "TokenBurnTransaction": "TokenBurnTransactionBody",
    "TokenAssociateTransaction": "TokenAssociateTransactionBody",
    "TokenDissociateTransaction": "TokenDissociateTransactionBody",
    "TokenMintTransaction": "TokenMintTransactionBody",
}

if __name__ == "__main__":
    step3_module = load_module(STEP3_FILE, "step3_token_classes")
    step4_module = load_module(STEP4_FILE, "step4_proto_attributes")
    proto_mappings = getattr(step4_module, "proto_mappings", {})

    print("\n📦 Proto mappings available:")
    for k in sorted(proto_mappings.keys()):
        print(" -", k)

    for sdk_module_name, sdk_class_name in SDK_MODULE_CLASS_MAP.items():
        sdk_module = getattr(step3_module, sdk_module_name, None)
        sdk_class_info = getattr(sdk_module, sdk_class_name, None) if sdk_module else {'attributes': [], 'setters': [], 'other_methods': []}
        sdk_class_info.setdefault('other_methods', [])

        proto_class_name = TRANSACTION_PROTO_MAP.get(sdk_class_name, "")
        proto_info = proto_mappings.get(proto_class_name)
        if proto_info is None:
            print(f"\n⚠️ Proto mapping missing for {proto_class_name} (SDK {sdk_class_name})")
            proto_info = {'attributes': [], 'setters': []}

        actual_proto_attrs = [map_proto_to_sdk(a) for a in proto_info['attributes']]
        predicted_setters = predicted_proto_setters(proto_info['attributes'])

        sdk_methods = sdk_class_info['setters'] + sdk_class_info['other_methods']

        missing_attrs = [a for a in actual_proto_attrs if a not in sdk_class_info['attributes']]
        missing_setters = [s for s in predicted_setters if s not in sdk_methods]

        # Detect extra SDK helpers beyond predicted setters
        extra_sdk_methods = [m for m in sdk_methods if m not in predicted_setters]

        # Logging
        print(f"\n💠 {sdk_class_name} vs {proto_class_name}")
        print("✅ SDK Attributes:", sdk_class_info['attributes'])
        print("✅ SDK Setters:", sdk_class_info['setters'])
        print("✅ SDK Other Methods:", sdk_class_info['other_methods'])
        print("📦 Actual Proto Attributes:", actual_proto_attrs)
        print("📦 Predicted Proto Setters:", predicted_setters)

        if missing_attrs or missing_setters:
            print("⚠️ Missing in SDK:")
            if missing_attrs:
                print(" - Attributes:", missing_attrs)
            if missing_setters:
                print(" - Predicted Setters / Methods:", missing_setters)
        else:
            print("✅ SDK fully covers proto attributes and predicted setters")

        if extra_sdk_methods:
            print("✨ Extra SDK methods beyond proto setters:", extra_sdk_methods)
