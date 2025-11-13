"""
Step 4: Extract all protobuf message classes and enums from token proto modules.
Generates proto_mappings[class_name] -> {attributes, setters} for messages
and proto_enums[enum_name] -> {values} for enums.
"""

import importlib
from pathlib import Path
from steps_2_extracted_token_proto_imports import token_proto_map

OUTPUT_FILE = Path(__file__).parent / "steps_4_token_classes_proto_attributes.py"

proto_mappings = {}
proto_enums = {}

def extract_all_protos(module):
    """
    Recursively extract all protobuf messages and enums from a module.
    Returns:
        messages: dict[class_name] = [field names]
        enums: dict[enum_name] = [enum value names]
    """
    messages = {}
    enums = {}

    def visit(obj):
        try:
            if hasattr(obj, "DESCRIPTOR"):
                # Message class
                if hasattr(obj.DESCRIPTOR, "fields"):
                    messages[obj.DESCRIPTOR.name] = [f.name for f in obj.DESCRIPTOR.fields]
                # Enum class
                elif hasattr(obj.DESCRIPTOR, "values"):
                    enums[obj.DESCRIPTOR.name] = [v.name for v in obj.DESCRIPTOR.values]
        except Exception:
            pass

        # Recurse into nested classes
        for subname, subobj in vars(obj).items():
            if isinstance(subobj, type):
                visit(subobj)

    for name, obj in vars(module).items():
        if isinstance(obj, type):
            visit(obj)

    return messages, enums

def main():
    global proto_mappings, proto_enums

    for token_module, proto_entries in token_proto_map.items():
        for proto_module, proto_class in proto_entries:
            # Clean double prefixes if they exist
            if proto_module.startswith("hiero_sdk_python.hapi.services.hiero_sdk_python.hapi.services"):
                proto_module = proto_module[len("hiero_sdk_python.hapi.services."):]

            try:
                mod = importlib.import_module(proto_module)
            except Exception as e:
                print(f"❌ Failed to import {proto_module}: {e}")
                continue

            messages = {}
            enums = {}

            if proto_class:
                cls = getattr(mod, proto_class, None)
                if cls is not None:
                    # Extract messages/enums from specific class
                    m, e = extract_all_protos(cls)
                    messages.update(m)
                    enums.update(e)
                else:
                    print(f"⚠️ Class {proto_class} not found in {proto_module}")
            else:
                # Extract all messages/enums from module
                m, e = extract_all_protos(mod)
                messages.update(m)
                enums.update(e)

            # Add messages to proto_mappings
            for cls_name, fields in messages.items():
                proto_mappings[cls_name] = {
                    "attributes": fields,
                    "setters": [f"set_{f}" for f in fields]
                }

            # Add enums to proto_enums
            for enum_name, values in enums.items():
                proto_enums[enum_name] = {"values": values}

    # Write output to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated proto attributes and setters\n\n")
        f.write("proto_mappings = {\n")
        for cls_name, data in sorted(proto_mappings.items()):
            f.write(f"    '{cls_name}': {{\n")
            f.write("        'attributes': [\n")
            for a in data['attributes']:
                f.write(f"            '{a}',\n")
            f.write("        ],\n")
            f.write("        'setters': [\n")
            for s in data['setters']:
                f.write(f"            '{s}',\n")
            f.write("        ]\n")
            f.write("    },\n")
        f.write("}\n\n")

        f.write("# Auto-generated proto enums\n\n")
        f.write("proto_enums = {\n")
        for enum_name, data in sorted(proto_enums.items()):
            f.write(f"    '{enum_name}': {{\n")
            f.write("        'values': [\n")
            for v in data['values']:
                f.write(f"            '{v}',\n")
            f.write("        ]\n")
            f.write("    },\n")
        f.write("}\n")

    print(f"✅ Proto mappings written to {OUTPUT_FILE}")
    print(f"✅ Total message classes extracted: {len(proto_mappings)}")
    print(f"✅ Total enums extracted: {len(proto_enums)}")

if __name__ == "__main__":
    main()
