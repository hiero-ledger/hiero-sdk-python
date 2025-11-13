# scripts/generate_transactions_mapping.py
import inspect
from pathlib import Path
import importlib
import ast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKENS_DIR = PROJECT_ROOT / "src" / "hiero_sdk_python" / "tokens"
OUTPUT_FILE = PROJECT_ROOT / "scripts" / "transactions_mapping.py"

def find_proto_import(file_path):
    """Parse transaction file to find the protobuf import."""
    with open(file_path, "r") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("hiero_sdk_python.hapi.services"):
                for alias in node.names:
                    if alias.name.endswith("TransactionBody"):
                        return node.module, alias.name
    return None, None

transactions_mapping = {}
unmatched_transactions = []

# Keep track of modules to import
token_modules_set = set()
proto_modules_set = set()

token_files = list(TOKENS_DIR.glob("token_*_transaction.py"))

for token_file in token_files:
    module_name = f"hiero_sdk_python.tokens.{token_file.stem}"
    token_modules_set.add(token_file.stem)
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        print(f"Failed to import {module_name}: {e}")
        continue

    # Find the Transaction class
    transaction_class = None
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if "Transaction" in [base.__name__ for base in obj.__bases__]:
            transaction_class = obj
            transaction_class_name = obj.__name__
            break

    if not transaction_class:
        continue

    # Find proto import
    proto_module_name, proto_class_name = find_proto_import(token_file)
    proto_cls_str = proto_class_name if proto_class_name else "None"
    if proto_module_name:
        proto_modules_set.add(proto_module_name)
    else:
        unmatched_transactions.append(transaction_class_name)
        proto_module_name = None

    transactions_mapping[transaction_class_name] = {
        "cls": f"{token_file.stem}.{transaction_class_name}",  # will become proper import
        "proto_cls": proto_cls_str,
        "proto_module": proto_module_name
    }

# Write to file
with open(OUTPUT_FILE, "w") as f:
    f.write("# Auto-generated transactions mapping\n\n")

    # Write token imports
    f.write("from hiero_sdk_python.tokens import (\n")
    for module in sorted(token_modules_set):
        f.write(f"    {module},\n")
    f.write(")\n\n")

    # Write proto imports
    f.write("from hiero_sdk_python.hapi.services import (\n")
    for module in sorted(proto_modules_set):
        # Only write the last part of the module for correct import
        short_module = module.split('.')[-1]
        f.write(f"    {short_module},\n")
    f.write(")\n\n")

    # Write TRANSACTIONS dictionary
    f.write("TRANSACTIONS = {\n")
    for k, v in transactions_mapping.items():
        cls_module, cls_name = v['cls'].split(".")
        cls_str = f"{cls_module}.{cls_name}"
        proto_cls_str = f"{v['proto_module'].split('.')[-1]}.{v['proto_cls']}" if v['proto_module'] else "None"
        f.write(f"    '{k}': {{'cls': {cls_str}, 'proto_cls': {proto_cls_str}}},\n")
    f.write("}\n\n")

    # Summary
    f.write("# Summary\n")
    f.write(f"TOTAL_TOKENS = {len(token_files)}\n")
    f.write(f"PROTO_IDENTIFIED = {len(token_files)-len(unmatched_transactions)}\n")
    f.write(f"UNMATCHED_TRANSACTIONS = {unmatched_transactions}\n")

print(f"Mapping written to {OUTPUT_FILE}")
