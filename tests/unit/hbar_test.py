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

@pytest.mark.parametrize(
    'invalid_amount',
    ['1', True, False, {}, object] 
)
def test_constructor_invalid_amount_type(invalid_amount):
    """Test creation with invalid type raise errors."""
    with pytest.raises(TypeError, match="Amount must be of type int, float, or Decimal"):
        Hbar(invalid_amount)

@pytest.mark.parametrize(
    'invalid_amount',
    [float('inf'), float('nan')] 
)
def test_constructor_non_finite_amount_value(invalid_amount):
    """Test creation raise errors for non finite amount."""
    with pytest.raises(ValueError, match="Hbar amount must be finite"):
        Hbar(invalid_amount)

def test_constructor_with_tinybar_unit():
    """Test creation with unit set to HbarUnit.TINYBAR."""
    hbar1 = Hbar(50, unit=HbarUnit.TINYBAR)
    assert hbar1.to_tinybars() == 50
    assert hbar1.to_hbars() == 0.0000005

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
        Hbar(0.1, unit=HbarUnit.TINYBAR)

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
        
def test_factory_methods():
    """Test the convenient from_X factory methods."""
    
    # from_microbars
    # 1 microbar = 100 tinybars
    result = Hbar.from_microbars(1)
    assert isinstance(result, Hbar)
    assert result.to_tinybars() == 100
    assert Hbar.from_microbars(1.5).to_tinybars() == 150
    assert Hbar.from_microbars(Decimal("2.5")).to_tinybars() == 250
    assert Hbar.from_microbars(0).to_tinybars() == 0
    assert Hbar.from_microbars(-10).to_tinybars() == -1_000
    # Verify equivalence with constructor
    assert Hbar.from_microbars(5) == Hbar(5, unit=HbarUnit.MICROBAR)

    # from_millibars
    # 1 millibar = 100,000 tinybars
    assert Hbar.from_millibars(1).to_tinybars() == 100_000
    assert Hbar.from_millibars(0).to_tinybars() == 0
    assert Hbar.from_millibars(-5).to_tinybars() == -500_000
    assert Hbar.from_millibars(Decimal("1.5")).to_tinybars() == 150_000

    # from_hbars
    # 1 hbar = 100,000,000 tinybars
    assert Hbar.from_hbars(1).to_tinybars() == 100_000_000
    assert Hbar.from_hbars(0.00000001).to_tinybars() == 1
    assert Hbar.from_hbars(0).to_tinybars() == 0
    assert Hbar.from_hbars(-10).to_tinybars() == -1_000_000_000
    assert Hbar.from_hbars(Decimal("5.5")).to_tinybars() == 550_000_000

    # from_kilobars
    # 1 kilobar = 1,000 hbars
    assert Hbar.from_kilobars(1).to_hbars() == 1_000
    assert Hbar.from_kilobars(0).to_hbars() == 0
    assert Hbar.from_kilobars(-2).to_hbars() == -2_000
    assert Hbar.from_kilobars(1).to_tinybars() == 100_000_000_000

    # from_megabars
    # 1 megabar = 1,000,000 hbars
    assert Hbar.from_megabars(1).to_hbars() == 1_000_000
    assert Hbar.from_megabars(0).to_hbars() == 0
    assert Hbar.from_megabars(-1).to_hbars() == -1_000_000
    assert Hbar.from_megabars(1).to_tinybars() == 100_000_000_000_000

    # from_gigabars
    # 1 gigabar = 1,000,000,000 hbars
    assert Hbar.from_gigabars(1).to_hbars() == 1_000_000_000
    assert Hbar.from_gigabars(0).to_hbars() == 0
    assert Hbar.from_gigabars(-1).to_hbars() == -1_000_000_000
    assert Hbar.from_gigabars(1).to_tinybars() == 100_000_000_000_000_000


# NEW TESTS: Coverage improvements for issue #1447
# ---------------------------------------------------------------------------

def test_from_tinybars_rejects_non_int():
    """from_tinybars() should reject non-integer input."""
    with pytest.raises(TypeError, match="tinybars must be an int"):
        Hbar.from_tinybars(1.5)

    with pytest.raises(TypeError, match="tinybars must be an int"):
        Hbar.from_tinybars("1000")

    with pytest.raises(TypeError, match="tinybars must be an int"):
        Hbar.from_tinybars(Decimal("1000"))



@pytest.mark.parametrize("other", [1, 1.0, "1", None])
def test_comparison_with_non_hbar_raises_type_error(other):
    """Ordering comparisons with non-Hbar types should raise TypeError."""
    h = Hbar(1)

    with pytest.raises(TypeError):
        _ = h < other

    with pytest.raises(TypeError):
        _ = h > other

    with pytest.raises(TypeError):
        _ = h <= other

    with pytest.raises(TypeError):
        _ = h >= other



def test_str_formatting_and_negatives():
    """String representation should use fixed 8 decimal places."""
    assert str(Hbar(1)) == "1.00000000 ℏ"
    assert str(Hbar(-1)) == "-1.00000000 ℏ"


def test_repr_contains_class_name_and_value():
    """repr() should include class name and value."""
    h = Hbar(2)
    r = repr(h)

    assert r.startswith("Hbar(")
    assert "2" in r



def test_hash_consistency_for_equal_values():
    """Equal Hbar values must have identical hashes."""
    h1 = Hbar(1)
    h2 = Hbar(1)

    assert h1 == h2
    assert hash(h1) == hash(h2)

    values = {h1, h2}
    assert len(values) == 1

    d = {h1: "value1"}
    d[h2] = "value2"
    assert len(d) == 1
    assert d[h1] == "value2"

    

@pytest.mark.parametrize(
    'invalid_tinybars',
    ['1', 0.1, Decimal('0.1'), True, False, object, {}]
)
def test_from_tinybars_invalid_type_param(invalid_tinybars):
    """Test from_tinybar method raises error if the type is not int."""
    with pytest.raises(TypeError, match=re.escape("tinybars must be an int.")):
        Hbar.from_tinybars(invalid_tinybars)