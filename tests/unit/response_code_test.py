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


@pytest.mark.parametrize(
    ("code", "expected_name"),
    [
        (86, "INVALID_RECEIVE_RECORD_THRESHOLD"),
        (87, "INVALID_SEND_RECORD_THRESHOLD"),
        (284, "INVALID_PROXY_ACCOUNT_ID"),
        (291, "CANNOT_APPROVE_FOR_ALL_FUNGIBLE_COMMON"),
        (296, "SPENDER_ACCOUNT_REPEATED_IN_ALLOWANCES"),
        (297, "REPEATED_SERIAL_NUMS_IN_NFT_ALLOWANCES"),
        (302, "REPEATED_ALLOWANCES_TO_DELETE"),
    ],
)
def test_codes_deprecated_in_the_protobuf_are_still_defined(code: int, expected_name: str) -> None:
    """Codes marked [deprecated = true] in the proto remain defined, as the proto still defines them."""
    member = ResponseCode(code)
    assert member.name == expected_name
    assert member is ResponseCode[expected_name]
    # Deprecated in the protobuf is not the same as an alias: these are members in their own right.
    assert expected_name in {m.name for m in ResponseCode}


def test_unknown_code_still_falls_back() -> None:
    """The _missing_ hook is unaffected by the corrected members."""
    unknown = ResponseCode(9999)
    assert unknown.name == "UNKNOWN_CODE_9999"
    assert unknown.is_unknown
    assert not ResponseCode.SUCCESS.is_unknown
