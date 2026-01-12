from hiero_sdk_python.hapi.services.basic_types_pb2 import Key

def format_key(key: Key) -> str:
    """
    This function handles both SDK PublicKey objects and protobuf Key messages.
    If a method is only available on protobuf message objects, not on
    SDK wrapper classes like PublicKey. To ensure compatibility with both types,
    we check if the key is an SDK wrapper and convert it to its protobuf
    representation before calling it.
    
    Converts a protobuf Key into a nicely formatted string:
      - If key is None, return "None"
      - If ed25519, show "ed25519(hex-encoded)"
      - If thresholdKey, keyList, or something else, show a short label.
    """
    if key is None:
        return "None"
    

    # Issue: if PublicKey objects don't have certain method e.g., HasField() (protobuf-only)
    # Solution: Check for _to_proto() method and convert before calling it
    if hasattr(key, '_to_proto'):
        key = key._to_proto() # Handle PublicKey objects (convert to proto first)
    if key.HasField("ed25519"):
        return f"ed25519({key.ed25519.hex()})"
    elif key.HasField("thresholdKey"):
        return "thresholdKey(...)"
    elif key.HasField("keyList"):
        return "keyList(...)"
    elif key.HasField("contractID"):
        return f"contractID({key.contractID})"

    return str(key).replace("\n", " ")
