from decimal import Decimal
import re
import pytest

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hbar_unit import HbarUnit

pytestmark = pytest.mark.unit

def test_constructor():
    """Test creation with int, float, and Decimal values in hbars."""
    hbar1 = Hbar(50)
    assert hbar1.to_tinybars() == 5_000_000_000
    assert hbar1.to_hbars() == 50

    hbar2 = Hbar(0.5)
    assert hbar2.to_tinybars() == 50_000_000
    assert hbar2.to_hbars() == 0.5

    hbar3 = Hbar(Decimal("0.5"))
    assert hbar3.to_tinybars() == 50_000_000
    assert hbar3.to_hbars() == 0.5

def test_constructor_in_tinybars():
    """Test creation directly in tinybars."""
    hbar1 = Hbar(50, in_tinybars=True)
    assert hbar1.to_tinybars() == 50
    assert hbar1.to_hbars() == 0.0000005

    # If in_tinybars is False (Default)
    hbar2 = Hbar(50, in_tinybars=False)
    assert hbar2.to_tinybars() == 5_000_000_000
    assert hbar2.to_hbars() == 50

def test_constructor_with_unit():
    """Test creation directly in tinybars."""
    hbar1 = Hbar(50, unit=HbarUnit.TINYBAR)
    assert hbar1.to_tinybars() == 50
    assert hbar1.to_hbars() == 0.0000005

    hbar2 = Hbar(50, unit=HbarUnit.MICROBAR)
    assert hbar2.to_tinybars() == 5000
    assert hbar2.to_hbars() == 0.00005

    hbar3 = Hbar(50, unit=HbarUnit.MILLIBAR)
    assert hbar3.to_tinybars() == 5_000_000
    assert hbar3.to_hbars() == 0.05

    hbar4 = Hbar(50, unit=HbarUnit.HBAR) # Default
    assert hbar4.to_tinybars() == 5_000_000_000
    assert hbar4.to_hbars() == 50

    hbar5 = Hbar(50, unit=HbarUnit.KILOBAR)
    assert hbar5.to_tinybars() == 5_000_000_000_000
    assert hbar5.to_hbars() == 50_000

    hbar6 = Hbar(50, unit=HbarUnit.MEGABAR)
    assert hbar6.to_tinybars() == 5_000_000_000_000_000
    assert hbar6.to_hbars() == 50_000_000

    hbar7 = Hbar(50, unit=HbarUnit.GIGABAR)
    assert hbar7.to_tinybars() == 5_000_000_000_000_000_000
    assert hbar7.to_hbars() == 50_000_000_000

def test_constructor_fractional_tinybar():
    """Test creation with fractional tinybars."""
    with pytest.raises(ValueError, match="Fractional tinybar value not allowed"):
        Hbar(0.1, in_tinybars=True)

def test_constructor_invalid_type():
    """Test creation of Hbar with invalid type."""
    with pytest.raises(TypeError, match="Amount must be of type int, float, or Decimal"):
        Hbar('10')

def test_from_string():
    """Test creation of HBAR from valid string"""
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
    """Test creation of HBAR from invalid string"""
    with pytest.raises(ValueError, match=re.escape(f"Invalid Hbar format: '{invalid_str}'")):
        Hbar.from_string(invalid_str)


def test_creation_using_of_method():
    """Test creation of HBAR using of method"""
    assert Hbar.of(50, HbarUnit.TINYBAR).to_tinybars() == 50
    assert Hbar.of(50, HbarUnit.HBAR).to_tinybars() == 5_000_000_000
    assert Hbar.of(50, HbarUnit.MICROBAR).to_tinybars() == 5000
    assert Hbar.of(50, HbarUnit.MILLIBAR).to_tinybars() == 5_000_000
    assert Hbar.of(50, HbarUnit.KILOBAR).to_tinybars() == 5_000_000_000_000
    assert Hbar.of(50, HbarUnit.MEGABAR).to_tinybars() == 5_000_000_000_000_000
    assert Hbar.of(50, HbarUnit.GIGABAR).to_tinybars() == 5_000_000_000_000_000_000

def test_to_unit():
    assert Hbar(50).to(HbarUnit.HBAR) == 50
    assert Hbar(50).to(HbarUnit.TINYBAR) == 5_000_000_000
    assert Hbar(50).to(HbarUnit.MICROBAR) == 50_000_000
    assert Hbar(50).to(HbarUnit.MILLIBAR) == 50_000
    assert Hbar(50).to(HbarUnit.KILOBAR) == 0.05
    assert Hbar(50).to(HbarUnit.MEGABAR) == 0.00005
    assert Hbar(50).to(HbarUnit.GIGABAR) == 0.00000005

def test_negated():
    """Test negation of Hbar values."""
    hbar = Hbar(10)
    neg_hbar = hbar.negated()
    assert neg_hbar.to_tinybars() == -1_000_000_000

    # Check that again become equal to original
    assert neg_hbar.negated() == hbar

def test_hbar_constant():
    assert Hbar.ZERO.to_hbars() == 0
    assert Hbar.MAX.to_hbars() == 50_000_000_000
    assert Hbar.MIN.to_hbars() == -50_000_000_000

def test_comparison():
    """Test comparison and equality operators."""
    h1 = Hbar(1)
    h2 = Hbar(2)
    h3 = Hbar(1)

    assert h1 == h3
    assert h1 != h2
    assert h1 < h2
    assert h2 > h1
    assert h1 <= h3
    assert h2 >= h1

    # Comparison without Hbar returns NotImplemented
    assert (h1 == 5) is False
    with pytest.raises(TypeError):
        _ = h1 < 5