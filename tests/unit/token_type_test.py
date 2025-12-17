import pytest
from hiero_sdk_python.tokens.token_type import TokenType

pytestmark = pytest.mark.unit

def test_members():
    assert TokenType.FUNGIBLE_COMMON.value == 0
    assert TokenType.NON_FUNGIBLE_UNIQUE.value == 1

def test_name():
    assert TokenType.FUNGIBLE_COMMON.name == "FUNGIBLE_COMMON"
    assert TokenType.NON_FUNGIBLE_UNIQUE.name == "NON_FUNGIBLE_UNIQUE"

