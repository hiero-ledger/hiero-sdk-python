"""
Parity test between the hand-maintained ResponseCode enum in the SDK
and the auto-generated ResponseCodeEnum from protobuf definitions.

Ensures that:
- Every status code defined in protobuf exists in the SDK ResponseCode enum.
- Every code in the SDK ResponseCode enum exists in protobuf.
- Numeric values match 1:1 across all codes.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.hapi.services.response_code_pb2 import ResponseCodeEnum
from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.unit


def test_response_code_parity_with_protobuf():
    """Verify exact 1:1 parity between ResponseCode and ResponseCodeEnum."""
    sdk_codes = {code.name: code.value for code in ResponseCode}
    proto_codes = dict(ResponseCodeEnum.items())

    missing_in_sdk = set(proto_codes.keys()) - set(sdk_codes.keys())
    extra_in_sdk = set(sdk_codes.keys()) - set(proto_codes.keys())

    assert not missing_in_sdk, (
        f"ResponseCode is missing {len(missing_in_sdk)} codes present in protobuf: {sorted(missing_in_sdk)}"
    )
    assert not extra_in_sdk, (
        f"ResponseCode contains {len(extra_in_sdk)} codes not found in protobuf: {sorted(extra_in_sdk)}"
    )

    value_mismatches = {
        name: {"sdk_value": sdk_codes[name], "proto_value": proto_codes[name]}
        for name in proto_codes
        if sdk_codes.get(name) != proto_codes[name]
    }

    assert not value_mismatches, f"ResponseCode value mismatches found: {value_mismatches}"


def test_canonical_codes_consistency():
    """Verify common canonical status codes maintain expected integer values."""
    assert ResponseCode.OK == 0
    assert ResponseCode.INVALID_TRANSACTION == 1
    assert ResponseCode.SUCCESS == 22
    assert ResponseCode.TRANSACTION_EXPIRED == 4
