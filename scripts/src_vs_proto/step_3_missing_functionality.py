# scripts/missing_functionality.py
import inspect
from step_2_transactions_mapping import TRANSACTIONS

# Helper functions for terminal styling
def bold(text):
    return f"\033[1m{text}\033[0m"

def red(text):
    return f"\033[91m{text}\033[0m"

def green(text):
    return f"\033[92m{text}\033[0m"

def get_transaction_methods(cls):
    return set(func for func, _ in inspect.getmembers(cls, predicate=inspect.isfunction))

def get_transaction_attributes(cls):
    init_sig = inspect.signature(cls.__init__)
    return set(init_sig.parameters.keys()) - {'self'}

def get_proto_fields(proto_cls):
    return set(proto_cls.DESCRIPTOR.fields_by_name.keys())

def check_transaction(transaction_cls, proto_cls):
    proto_fields = get_proto_fields(proto_cls)
    methods = get_transaction_methods(transaction_cls)
    attributes = get_transaction_attributes(transaction_cls)
    
    actual_setters = {m for m in methods if m.startswith("set_")}
    missing_setters = {f"set_{field}" for field in proto_fields} - actual_setters

    actual_attrs = attributes
    missing_attrs = proto_fields - actual_attrs
    
    return {
        "transaction": transaction_cls.__name__,
        "proto_fields": proto_fields,
        "attributes": attributes,
        "actual_attrs": actual_attrs,
        "methods": methods,
        "actual_setters": actual_setters,
        "missing_setters": missing_setters,
        "missing_attrs": missing_attrs
    }

def main():
    for name, mapping in TRANSACTIONS.items():
        cls = mapping["cls"]
        proto_cls = mapping["proto_cls"]
        result = check_transaction(cls, proto_cls)

        print(f"\n{bold(f'=== {name} ===')}")
        print(f"{bold('Proto fields:')} {sorted(result['proto_fields'])}")
        print(f"{bold('Attributes in __init__:')} {sorted(result['attributes'])}")

        print(f"\n{bold('Actual found')}")
        print(f"  {bold('Attributes:')} {green(sorted(result['actual_attrs']))}")
        print(f"  {bold('Setter methods:')} {green(sorted(result['actual_setters']))}")

        print(f"\n{bold('Missing')}")
        print(f"  {bold('Setter methods:')} {red(sorted(result['missing_setters']))}")
        print(f"  {bold('Attributes:')} {red(sorted(result['missing_attrs']))}")

if __name__ == "__main__":
    main()
