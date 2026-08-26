from __future__ import annotations

import pytest

from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("code", "expected_name"),
    [
        # Previously swapped with each other (356 <-> 357).
        (356, "SERVICE_ENDPOINTS_EXCEEDED_LIMIT"),
        (357, "INVALID_IPV4_ADDRESS"),
        # Previously carried a misspelled or non-canonical name.
        (344, "INVALID_GOSSIP_CA_CERTIFICATE"),
        (363, "PENDING_AIRDROP_ID_LIST_TOO_LONG"),
        (369, "INVALID_TOKEN_IN_PENDING_AIRDROP"),
        # Previously missing entirely, so the network's code surfaced as UNKNOWN_CODE_113.
        (113, "RECEIVER_SIG_REQUIRED"),
    ],
)
def test_code_resolves_to_canonical_proto_name(code: int, expected_name: str) -> None:
    """Each corrected code resolves to the name used in response_code.proto."""
    member = ResponseCode(code)
    assert member.name == expected_name
    assert member is ResponseCode[expected_name]


@pytest.mark.parametrize(
    ("deprecated_name", "canonical_name", "value"),
    [
        ("INVALID_GOSSIP_CAE_CERTIFICATE", "INVALID_GOSSIP_CA_CERTIFICATE", 344),
        ("MAX_PENDING_AIRDROP_ID_EXCEEDED", "PENDING_AIRDROP_ID_LIST_TOO_LONG", 363),
        ("INVALID_TOKEN_ID_PENDING_AIRDROP", "INVALID_TOKEN_IN_PENDING_AIRDROP", 369),
    ],
)
def test_renamed_codes_keep_working_deprecated_alias(deprecated_name: str, canonical_name: str, value: int) -> None:
    """The old names still resolve, so existing user code keeps working."""
    alias = getattr(ResponseCode, deprecated_name)
    assert alias == value
    assert alias is getattr(ResponseCode, canonical_name)
    # An alias is reachable by name but is not a member in its own right.
    assert deprecated_name in ResponseCode.__members__
    assert deprecated_name not in {member.name for member in ResponseCode}


def test_unknown_code_still_falls_back() -> None:
    """The _missing_ hook is unaffected by the corrected members."""
    unknown = ResponseCode(9999)
    assert unknown.name == "UNKNOWN_CODE_9999"
    assert unknown.is_unknown
    assert not ResponseCode.SUCCESS.is_unknown
