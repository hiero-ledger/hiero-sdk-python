"""Parity tests between the SDK ResponseCode IntEnum and generated ResponseCodeEnum.

Ensures exact name-to-value parity in both directions between ResponseCode
and response_code_pb2.ResponseCodeEnum to prevent and catch drift (such as #2608).
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.hapi.services.response_code_pb2 import ResponseCodeEnum
from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.unit


def test_proto_to_sdk_response_code_parity() -> None:
    """Check that every proto ResponseCodeEnum entry maps to a matching ResponseCode member."""
    proto_map = dict(ResponseCodeEnum.items())
    mismatches: list[str] = []

    for name, proto_value in proto_map.items():
        if name not in ResponseCode.__members__:
            mismatches.append(f"Missing in ResponseCode: {name} (proto={proto_value}, sdk=None)")
        else:
            sdk_value = ResponseCode.__members__[name].value
            if sdk_value != proto_value:
                mismatches.append(f"Value mismatch for {name}: proto={proto_value}, sdk={sdk_value}")

    assert not mismatches, "Proto -> SDK ResponseCode parity mismatches detected:\n" + "\n".join(mismatches)


def test_sdk_to_proto_response_code_parity() -> None:
    """Check that every canonical SDK ResponseCode member maps to a matching proto enum entry."""
    proto_map = dict(ResponseCodeEnum.items())
    mismatches: list[str] = []

    # Iterating the enum class directly yields only canonical members and skips
    # aliases. This tolerates intentional backwards-compatibility aliases
    # (such as those introduced in #2608) without hiding real drift in canonical definitions.
    for member in ResponseCode:
        if member.name not in proto_map:
            mismatches.append(f"Missing in proto enum: {member.name} (sdk={member.value}, proto=None)")
        else:
            proto_value = proto_map[member.name]
            if member.value != proto_value:
                mismatches.append(f"Value mismatch for {member.name}: sdk={member.value}, proto={proto_value}")

    assert not mismatches, "SDK -> Proto ResponseCode parity mismatches detected:\n" + "\n".join(mismatches)
