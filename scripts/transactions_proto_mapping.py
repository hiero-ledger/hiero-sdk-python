# scripts/generate_transactions_mapping.py
import inspect
from pathlib import Path
import importlib
import ast

# -----------------------------
# Hardcoded paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKENS_DIR = PROJECT_ROOT / "src" / "hiero_sdk_python" / "tokens"

# -----------------------------
# Helpers
# -----------------------------
def find_proto_import(file_path):
    """
    Parse the transaction file and find the protobuf import.
    Returns (module_name, class_name) for the proto, e.g.,
    ('hiero_sdk_python.hapi.services.token_revoke_kyc_pb2', 'TokenRevokeKycTransactionBody')
    """
    with open(file_path, "r") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("hiero_sdk_python.hapi.services"):
                for alias in node.names:
                    if alias.name.endswith("TransactionBody"):
                        proto_module = node.module
                        proto_class = alias.name
                        return proto_module, proto_class
    return None, None

# -----------------------------
# Scan tokens directory
# -----------------------------
transactions_mapping = {}
unmatched_transactions = []

token_files = list(TOKENS_DIR.glob("token_*_transaction.py"))
print(f"Found {len(token_files)} token modules in {TOKENS_DIR}")

for token_file in token_files:
    module_name = f"hiero_sdk_python.tokens.{token_file.stem}"
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
        print(f"No Transaction class found in {module_name}")
        continue

    # Parse the file to find the proto import
    proto_module_name, proto_class_name = find_proto_import(token_file)
    if not proto_module_name or not proto_class_name:
        print(f"Could not detect proto for {transaction_class_name}")
        proto_cls_str = "None"
        unmatched_transactions.append(transaction_class_name)
    else:
        proto_cls_str = f"{proto_module_name}.{proto_class_name}"

    # Store mapping
    transactions_mapping[transaction_class_name] = {
        "cls": f"{module_name}.{transaction_class_name}",
        "proto_cls": proto_cls_str
    }

# -----------------------------
# Print the mapping in Python dict format
# -----------------------------
print("\nTRANSACTIONS = {")
for k, v in transactions_mapping.items():
    print(f"    '{k}': {{'cls': {v['cls']}, 'proto_cls': {v['proto_cls']}}},")
print("}")

# -----------------------------
# Summary / checks
# -----------------------------
total_tokens = len(token_files)
total_protos = total_tokens - len(unmatched_transactions)
print(f"\nSummary:")
print(f"Total token modules scanned: {total_tokens}")
print(f"Protos successfully identified: {total_protos}")
print(f"Transactions without matched proto: {len(unmatched_transactions)}")
if unmatched_transactions:
    print(f"  - {', '.join(unmatched_transactions)}")
