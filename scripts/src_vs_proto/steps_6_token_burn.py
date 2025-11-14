#!/usr/bin/env python3
"""
Step 6 (Fixed Dynamic): Compare *all* token transaction SDK classes with proto attributes.
Now properly finds nested entries like token_burn_transaction.TokenBurnTransaction.
"""

from pathlib import Path
import importlib.util
import sys
import re

STEP3_FILE = Path(__file__).resolve().parent / "steps_3_token_classes_info_readable.py"
STEP4_FILE = Path(__file__).resolve().parent / "steps_4_token_classes_proto_attributes.py"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


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
    "set_account": "set_account_id",
}


def map_proto_to_sdk(proto_attr: str) -> str:
    return PROTO_TO_SDK_MAP.get(proto_attr, camel_to_snake(proto_attr))


def predicted_proto_setters(proto_attrs):
    return [f"set_{map_proto_to_sdk(a)}" for a in proto_attrs]


def find_proto_class_name(sdk_class_name: str, proto_mappings: dict):
    base = sdk_class_name.replace("Transaction", "TransactionBody")
    if base in proto_mappings:
        return base
    for proto_name in proto_mappings.keys():
        if proto_name.lower().startswith(sdk_class_name.lower().replace("transaction", "")):
            return proto_name
    return None


def collect_sdk_classes(step3_module):
    """
    Recursively collect dict objects representing SDK classes
    from the parsed Step 3 module.
    """
    sdk_classes = {}
    for name, val in vars(step3_module).items():
        if isinstance(val, dict) and "attributes" in val and "setters" in val:
            sdk_classes[name] = val
        elif isinstance(val, type(step3_module)):  # submodule-like object
            for subname, subval in vars(val).items():
                if isinstance(subval, dict) and "attributes" in subval:
                    sdk_classes[f"{name}.{subname}"] = subval
    return sdk_classes


if __name__ == "__main__":
    step3_module = load_module(STEP3_FILE, "step3_token_classes")
    step4_module = load_module(STEP4_FILE, "step4_proto_attributes")
    proto_mappings = getattr(step4_module, "proto_mappings", {})

    print("\n📦 Proto mappings available:")
    for k in sorted(proto_mappings.keys()):
        print(" -", k)

    sdk_classes = collect_sdk_classes(step3_module)
    print(f"\n🔍 Found {len(sdk_classes)} SDK token transaction classes to compare.\n")

    for full_cls_name, sdk_class_info in sorted(sdk_classes.items()):
        sdk_class_name = full_cls_name.split(".")[-1]
        proto_class_name = find_proto_class_name(sdk_class_name, proto_mappings)

        if not proto_class_name:
            print(f"\n⚠️ No proto mapping found for SDK class {sdk_class_name}")
            continue

        proto_info = proto_mappings.get(proto_class_name, {"attributes": [], "setters": []})
        actual_proto_attrs = [map_proto_to_sdk(a) for a in proto_info["attributes"]]
        predicted_setters = predicted_proto_setters(proto_info["attributes"])

        sdk_attrs = sdk_class_info.get("attributes", [])
        sdk_methods = sdk_class_info.get("setters", []) + sdk_class_info.get("other_methods", [])

        missing_attrs = [a for a in actual_proto_attrs if a not in sdk_attrs]
        missing_setters = [s for s in predicted_setters if s not in sdk_methods]
        extra_sdk_methods = [m for m in sdk_methods if m not in predicted_setters]

        print(f"\n💠 {sdk_class_name} vs {proto_class_name}")
        print(f"{GREEN}SDK Attributes: {sdk_attrs}{RESET}")
        print(f"{GREEN}SDK Setters: {sdk_class_info.get('setters', [])}{RESET}")
        print("✅ SDK Other Methods:", sdk_class_info.get("other_methods", []))
        print("📦 Actual Proto Attributes:", actual_proto_attrs)
        print("📦 Predicted Proto Setters:", predicted_setters)

        if missing_attrs or missing_setters:
            print(f"{RED}⚠️ Missing in SDK:{RESET}")
            if missing_attrs:
                print(f"{RED} - Attributes: {missing_attrs}{RESET}")
            if missing_setters:
                print(f"{RED} - Predicted Setters / Methods: {missing_setters}{RESET}")
        else:
            print(f"{GREEN}✅ SDK fully covers proto attributes and predicted setters{RESET}")

        if extra_sdk_methods:
            print("✨ Extra SDK methods beyond proto setters:", extra_sdk_methods)
