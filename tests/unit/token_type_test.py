from __future__ import annotations

import pytest

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_type import TokenType


pytestmark = pytest.mark.unit


def test_members():
    """Test TokenType return valid values."""
    assert TokenType.FUNGIBLE_COMMON.value == 0
    assert TokenType.NON_FUNGIBLE_UNIQUE.value == 1


def test_name():
    """Test TokeType return valid names."""
    assert TokenType.FUNGIBLE_COMMON.name == "FUNGIBLE_COMMON"
    assert TokenType.NON_FUNGIBLE_UNIQUE.name == "NON_FUNGIBLE_UNIQUE"


@pytest.mark.parametrize(
    ("proto", "expected"),
    [
        (basic_types_pb2.TokenType.FUNGIBLE_COMMON, TokenType.FUNGIBLE_COMMON),
        (basic_types_pb2.NON_FUNGIBLE_UNIQUE, TokenType.NON_FUNGIBLE_UNIQUE),
    ],
)
def test_from_proto(proto, expected):
    """Test TokenType creation using protobuf message."""
    token_type = TokenType._from_proto(proto)
    assert token_type is not None
    assert token_type == expected


# @pytest.mark.parametrize(
#     "invalid_param",
#     ["1", 0.1, None, {}, (), True, basic_types_pb2.TokenSupplyType.FINITE]
# )
# def test_from_proto_with_invalid_value(invalid_param):
#     """Test TokenType creation using protobuf message."""
#     with pytest.raises(ValueError, match="Invalid TokenType"):
#         TokenType._from_proto(invalid_param)
