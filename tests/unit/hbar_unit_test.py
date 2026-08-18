from __future__ import annotations

import pytest

from hiero_sdk_python import HbarUnit


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("unit", "expected_symbol"),
    [
        (HbarUnit.TINYBAR, "tℏ"),
        (HbarUnit.MICROBAR, "μℏ"),
        (HbarUnit.MILLIBAR, "mℏ"),
        (HbarUnit.HBAR, "ℏ"),
        (HbarUnit.KILOBAR, "kℏ"),
        (HbarUnit.MEGABAR, "Mℏ"),
        (HbarUnit.GIGABAR, "Gℏ"),
    ],
)
def test_member_symbols(unit: HbarUnit, expected_symbol: str) -> None:
    """Verify that each HbarUnit enum member returns its expected unit symbol string."""
    assert unit.symbol == expected_symbol, (
        f"Wrong symbol for {unit.name}: expected {expected_symbol!r}, got {unit.symbol!r}"
    )


@pytest.mark.parametrize(
    ("unit", "expected_tinybar"),
    [
        (HbarUnit.TINYBAR, 1),
        (HbarUnit.MICROBAR, 10**2),
        (HbarUnit.MILLIBAR, 10**5),
        (HbarUnit.HBAR, 10**8),
        (HbarUnit.KILOBAR, 10**11),
        (HbarUnit.MEGABAR, 10**14),
        (HbarUnit.GIGABAR, 10**17),
    ],
)
def test_member_tinybar_factors(unit: HbarUnit, expected_tinybar: int) -> None:
    """Verify that each HbarUnit enum member returns its expected tinybar conversion factor."""
    assert unit.tinybar == expected_tinybar, (
        f"Wrong tinybar factor for {unit.name}: expected {expected_tinybar}, got {unit.tinybar}"
    )


@pytest.mark.parametrize(
    ("symbol", "expected_unit"),
    [
        ("tℏ", HbarUnit.TINYBAR),
        ("μℏ", HbarUnit.MICROBAR),
        ("mℏ", HbarUnit.MILLIBAR),
        ("ℏ", HbarUnit.HBAR),
        ("kℏ", HbarUnit.KILOBAR),
        ("Mℏ", HbarUnit.MEGABAR),
        ("Gℏ", HbarUnit.GIGABAR),
    ],
)
def test_from_string_valid(symbol: str, expected_unit: HbarUnit) -> None:
    """Verify that HbarUnit.from_string converts valid symbol strings to the expected HbarUnit member."""
    result = HbarUnit.from_string(symbol)
    assert isinstance(result, HbarUnit), f"Expected HbarUnit.from_string({symbol!r}) to return HbarUnit"
    assert result is expected_unit, f"Wrong unit for {symbol!r}: expected {expected_unit.name}, got {result.name}"


@pytest.mark.parametrize("invalid_symbol", ["", "h", "xyz"])
def test_from_string_invalid(invalid_symbol: str) -> None:
    """Verify that HbarUnit.from_string raises a ValueError for invalid symbol strings."""
    with pytest.raises(ValueError, match=f"^Invalid Hbar unit symbol: {invalid_symbol}$"):
        HbarUnit.from_string(invalid_symbol)


def test_name() -> None:
    """Verify that HbarUnit enum has all expected members and correct member name attributes."""
    members = list(HbarUnit)
    assert len(members) == 7, f"Expected 7 members in HbarUnit, found {len(members)}"
    assert HbarUnit.TINYBAR.name == "TINYBAR", f"Expected TINYBAR.name to be 'TINYBAR', got {HbarUnit.TINYBAR.name!r}"
    assert HbarUnit.MICROBAR.name == "MICROBAR", (
        f"Expected MICROBAR.name to be 'MICROBAR', got {HbarUnit.MICROBAR.name!r}"
    )
    assert HbarUnit.MILLIBAR.name == "MILLIBAR", (
        f"Expected MILLIBAR.name to be 'MILLIBAR', got {HbarUnit.MILLIBAR.name!r}"
    )
    assert HbarUnit.HBAR.name == "HBAR", f"Expected HBAR.name to be 'HBAR', got {HbarUnit.HBAR.name!r}"
    assert HbarUnit.KILOBAR.name == "KILOBAR", f"Expected KILOBAR.name to be 'KILOBAR', got {HbarUnit.KILOBAR.name!r}"
    assert HbarUnit.MEGABAR.name == "MEGABAR", f"Expected MEGABAR.name to be 'MEGABAR', got {HbarUnit.MEGABAR.name!r}"
    assert HbarUnit.GIGABAR.name == "GIGABAR", f"Expected GIGABAR.name to be 'GIGABAR', got {HbarUnit.GIGABAR.name!r}"
