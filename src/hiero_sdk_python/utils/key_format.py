from __future__ import annotations

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key as KeyProto


def format_key(key: Key | KeyProto | None) -> str:
    """
    Converts an SDK or protobuf Key into a nicely formatted string:
      - If key is None, return "None"
      - If ed25519, show "ed25519(hex-encoded)"
      - If thresholdKey, keyList, or something else, show a short label.
    """
    if key is None:
        return "None"

    if isinstance(key, Key):
        key = key.to_proto_key()
    if key.HasField("ed25519"):
        return f"ed25519({key.ed25519.hex()})"
    if key.HasField("thresholdKey"):
        return "thresholdKey(...)"
    if key.HasField("keyList"):
        return "keyList(...)"
    if key.HasField("contractID"):
        return f"contractID({key.contractID})"

    return str(key).replace("\n", " ")
