"""
Hashability tests for status enums that define a custom __eq__.

Defining __eq__ in a class body sets __hash__ = None unless __hash__ is
also defined — which had silently made these Enum members unhashable:
natural user code like `status in {TokenFreezeStatus.FROZEN}` raised
TypeError. These tests pin that every such enum is hashable and that its
hash is consistent with its int-accepting __eq__ (equal objects must hash
equally, so hash(MEMBER) == hash(MEMBER.value)).
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.system.freeze_type import FreezeType
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_key_validation import TokenKeyValidation
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus


pytestmark = pytest.mark.unit

STATUS_ENUMS = [
    TokenFreezeStatus,
    TokenKycStatus,
    TokenPauseStatus,
    FreezeType,
    TokenKeyValidation,
]

_IDS = [cls.__name__ for cls in STATUS_ENUMS]


@pytest.mark.parametrize("enum_cls", STATUS_ENUMS, ids=_IDS)
def test_members_are_hashable(enum_cls):
    """Every member must be hashable — usable in sets and as dict keys."""
    members = list(enum_cls)

    assert set(members) == set(members)
    assert members[0] in set(members)

    lookup = {member: member.name for member in members}
    assert lookup[members[0]] == members[0].name


@pytest.mark.parametrize("enum_cls", STATUS_ENUMS, ids=_IDS)
def test_hash_is_consistent_with_int_equality(enum_cls):
    """__eq__ equates members with their int value, so their hashes must
    match too — otherwise `member.value in {member}` would be False while
    `member.value == member` is True."""
    for member in enum_cls:
        assert member == member.value
        assert hash(member) == hash(member.value)
        assert member.value in {member}
        assert member in {member.value}
