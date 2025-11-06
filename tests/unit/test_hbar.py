from decimal import Decimal
import re
import pytest

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hbar_unit import HbarUnit


pytestmark = pytest.mark.unit


def test_constructor():
    hbar1 = Hbar(50)
    assert hbar1.to_tinybars() == 5_000_000_000
    assert hbar1.to_hbars() == 50

    hbar2 = Hbar(0.5)
    assert hbar2.to_tinybars() == 50_000_000
    assert hbar2.to_hbars() == 0.5

    hbar3 = Hbar(Decimal("0.5"))
    assert hbar3.to_tinybars() == 50_000_000
    assert hbar3.to_hbars() == 0.5

    hbar4 = Hbar(50, in_tinybars=True)
    assert hbar4.to_tinybars() == 50
    assert hbar4.to_hbars() == 0.0000005

def test_from_string():
    """Test create HBAR from valid string"""
    assert Hbar.from_string("1").to_tinybars() == 100_000_000
    assert Hbar.from_string("1 ℏ").to_tinybars() == 100_000_000
    assert Hbar.from_string("1.5 mℏ").to_tinybars() == 150_000
    assert Hbar.from_string("+1.5 mℏ").to_tinybars() == 150_000
    assert Hbar.from_string("-1.5 mℏ").to_tinybars() == -150_000
    assert Hbar.from_string("+3").to_tinybars() == 300_000_000
    assert Hbar.from_string("-3").to_tinybars() == -300_000_000

@pytest.mark.parametrize(
    'invalid_str', 
    [
        '1 ',
        '-1 ',
        '+1 ',
        '1.151 ',
        '-1.151 ',
        '+1.151 ',
        '1.',
        '1.151.',
        '.1',
        '1.151 uℏ',
        '1.151 h',
        'abcd'
    ]
)
def test_from_string_invalid(invalid_str):
    """Test create HBAR from invalid string"""
    with pytest.raises(ValueError, match=re.escape(f"Invalid Hbar format: '{invalid_str}'")):
        Hbar.from_string(invalid_str)


def test_from_amount():
    """Test create HBAR from valid string"""
    assert Hbar.from_amount(50, HbarUnit.HBAR).to_tinybars() == 5_000_000_000

def test_to_unit():
    assert Hbar(50).to(HbarUnit.HBAR) == 50
    assert Hbar(50).to(HbarUnit.TINYBAR) == 5_000_000_000
    assert Hbar(50).to(HbarUnit.MICROBAR) == 50_000_000
    assert Hbar(50).to(HbarUnit.MILLIBAR) == 50_000
    assert Hbar(50).to(HbarUnit.KILOBAR) == 0.05
    assert Hbar(50).to(HbarUnit.MEGABAR) == 0.00005
    assert Hbar(50).to(HbarUnit.GIGABAR) == 0.00000005

def test_hbar_constant():
    assert Hbar.ZERO.to_hbars() == 0
    assert Hbar.MAX.to_hbars() == 50_000_000_000
    assert Hbar.MIN.to_hbars() == -50_000_000_000