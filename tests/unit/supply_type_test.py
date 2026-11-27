from __future__ import annotations

import pytest

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.supply_type import SupplyType


pytestmark = pytest.mark.unit


def test_members():
    """Test SupplyType return valid value."""
    assert SupplyType.INFINITE.value == 0
    assert SupplyType.FINITE.value == 1


def test_name():
    """Test SupplyType return valid name."""
    assert SupplyType.INFINITE.name == "INFINITE"
    assert SupplyType.FINITE.name == "FINITE"


def test_supply_type_enum_members():
    """Test the SuppltType can get as list."""
    members = list(SupplyType)
    assert len(members) == 2
    assert SupplyType.INFINITE in members
    assert SupplyType.FINITE in members


@pytest.mark.parametrize(
    ("proto", "expected"),
    [
        (basic_types_pb2.TokenSupplyType.FINITE, SupplyType.FINITE),
        (basic_types_pb2.TokenSupplyType.INFINITE, SupplyType.INFINITE),
    ],
)
def test_from_proto(proto, expected):
    """Test SupplyType creation using protobuf message."""
    supply_type = SupplyType._from_proto(proto)
    assert supply_type is not None
    assert supply_type == expected
