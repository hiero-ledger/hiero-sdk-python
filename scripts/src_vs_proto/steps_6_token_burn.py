#!/usr/bin/env python3
"""
Step 6: Extract TokenBurnTransaction info from Step 3 output
         + corresponding proto attributes and setters from Step 4 output
"""

from pathlib import Path
import importlib.util
import sys

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

if __name__ == "__main__":
    # Load Step 3 (SDK classes)
    step3_module = load_module(STEP3_FILE, "step3_token_classes")
    tb_info = getattr(step3_module.token_burn_transaction, "TokenBurnTransaction", None)

    if tb_info:
        print("✅ TokenBurnTransaction info extracted from Step 3 output")
        print("Attributes:", tb_info['attributes'])
        print("Setters:", tb_info['setters'])
    else:
        print("⚠️ TokenBurnTransaction not found in Step 3 output")

    # Load Step 4 (proto mappings)
    step4_module = load_module(STEP4_FILE, "step4_proto_attributes")
    proto_info = getattr(step4_module, "proto_mappings", {}).get("TokenBurnTransactionBody", None)

    if proto_info:
        print("\n📦 Corresponding Proto: TokenBurnTransactionBody")
        print("Attributes:", proto_info['attributes'])
        print("Setters:", proto_info['setters'])
    else:
        print("⚠️ Proto TokenBurnTransactionBody not found in Step 4 output")
