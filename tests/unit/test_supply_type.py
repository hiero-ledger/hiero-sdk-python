import pytest
from hiero_sdk_python.tokens.supply_type import SupplyType

pytestmark = pytest.mark.unit

def test_members():
    assert SupplyType.INFINITE.value == 0
    assert SupplyType.FINITE.value == 1

def test_name():
    assert SupplyType.INFINITE.name == "INFINITE"
    assert SupplyType.FINITE.name == "FINITE"

def test_supply_type_enum_members():
    members = list(SupplyType)
    assert len(members) == 2
    assert SupplyType.INFINITE in members
    assert SupplyType.FINITE in members
