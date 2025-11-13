# scripts/missing_functionality.py
import inspect
from transactions_mapping import TRANSACTIONS

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
    
    missing_setters = {f"set_{field}" for field in proto_fields if f"set_{field}" not in methods}
    missing_attrs = proto_fields - attributes
    
    return {
        "transaction": transaction_cls.__name__,
        "proto_fields": proto_fields,
        "attributes": attributes,
        "methods": methods,
        "missing_setters": missing_setters,
        "missing_attrs": missing_attrs
    }

def main():
    for name, mapping in TRANSACTIONS.items():
        cls = mapping["cls"]
        proto_cls = mapping["proto_cls"]
        result = check_transaction(cls, proto_cls)

        print(f"\n=== {name} ===")
        print(f"Possible missing setter methods: {result['missing_setters']}")
        print(f"Possible missing attributes in __init__: {result['missing_attrs']}")

if __name__ == "__main__":
    main()
