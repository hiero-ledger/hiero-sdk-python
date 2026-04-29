"""Unit tests for ResponseCode enum mappings."""

from __future__ import annotations

import pytest

from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.unit


def test_hip_1137_response_codes_are_named_members():
    """HIP-1137 response codes should be first-class enum members."""
    assert ResponseCode(529) is ResponseCode.INVALID_REGISTERED_NODE_ID
    assert ResponseCode(530) is ResponseCode.INVALID_REGISTERED_ENDPOINT
    assert ResponseCode(531) is ResponseCode.REGISTERED_ENDPOINTS_EXCEEDED_LIMIT
    assert ResponseCode(532) is ResponseCode.INVALID_REGISTERED_ENDPOINT_ADDRESS
    assert ResponseCode(533) is ResponseCode.INVALID_REGISTERED_ENDPOINT_TYPE
    assert ResponseCode(534) is ResponseCode.REGISTERED_NODE_STILL_ASSOCIATED
    assert ResponseCode(535) is ResponseCode.MAX_REGISTERED_NODES_EXCEEDED


def test_unknown_response_code_still_uses_fallback_member():
    """Unknown integer values should continue to map to UNKNOWN_CODE_<n>."""
    unknown_code = ResponseCode(9999)
    assert unknown_code.is_unknown
    assert unknown_code.name == "UNKNOWN_CODE_9999"
