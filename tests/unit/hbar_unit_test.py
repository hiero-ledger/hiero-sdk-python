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
    assert unit.symbol == expected_symbol


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
    assert unit.tinybar == expected_tinybar


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
    assert HbarUnit.from_string(symbol) == expected_unit


@pytest.mark.parametrize("invalid_symbol", ["", "h", "xyz"])
def test_from_string_invalid(invalid_symbol: str) -> None:
    with pytest.raises(ValueError, match=f"^Invalid Hbar unit symbol: {invalid_symbol}$"):
        HbarUnit.from_string(invalid_symbol)


def test_name() -> None:
    assert len(list(HbarUnit)) == 7
    assert HbarUnit.TINYBAR.name == "TINYBAR"
    assert HbarUnit.MICROBAR.name == "MICROBAR"
    assert HbarUnit.MILLIBAR.name == "MILLIBAR"
    assert HbarUnit.HBAR.name == "HBAR"
    assert HbarUnit.KILOBAR.name == "KILOBAR"
    assert HbarUnit.MEGABAR.name == "MEGABAR"
    assert HbarUnit.GIGABAR.name == "GIGABAR"
