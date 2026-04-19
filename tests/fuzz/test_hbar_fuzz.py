from __future__ import annotations

import math

import pytest
from hypothesis import given

from hiero_sdk_python import Hbar, HbarUnit
from tests.fuzz.conftest import HbarConstructorCase, HbarStringCase, get_strategy


pytestmark = pytest.mark.fuzz


def _assert_hbar_invariants(value: Hbar, expected_tinybars: int) -> None:
    assert value.to_tinybars() == expected_tinybars
    assert math.isfinite(value.to_hbars())
    roundtripped = Hbar.from_tinybars(value.to_tinybars())
    assert roundtripped == value
    assert roundtripped.to_tinybars() == expected_tinybars


@given(case=get_strategy("hbar_valid_string"))
def test_hbar_from_string_accepts_valid_inputs(case: HbarStringCase) -> None:
    """Valid public Hbar strings must parse to the exact tinybar value."""
    parsed = Hbar.from_string(case.text)
    _assert_hbar_invariants(parsed, case.tinybars)


@given(text=get_strategy("hbar_invalid_string"))
def test_hbar_from_string_rejects_invalid_inputs(text: str) -> None:
    """Invalid Hbar strings must raise ValueError instead of partially parsing."""
    with pytest.raises(ValueError):
        Hbar.from_string(text)


@given(case=get_strategy("hbar_valid_constructor"))
def test_hbar_constructor_preserves_exact_value(case: HbarConstructorCase) -> None:
    """Valid constructor inputs must convert to the exact expected tinybar count."""
    parsed = Hbar(case.amount, unit=case.unit)
    _assert_hbar_invariants(parsed, case.tinybars)


@given(amount=get_strategy("hbar_invalid_nonfinite_float"))
def test_hbar_constructor_rejects_nonfinite_floats(amount: float) -> None:
    """The constructor must reject NaN and infinities explicitly."""
    with pytest.raises(ValueError):
        Hbar(amount)


@given(amount=get_strategy("fractional_tinybar_amount"))
def test_hbar_rejects_fractional_tinybars(amount: object) -> None:
    """Tinybar inputs are integral only; fractional values are invalid."""
    with pytest.raises(ValueError):
        Hbar(amount, unit=HbarUnit.TINYBAR)


@given(value=get_strategy("hbar_invalid_constructor_type"))
def test_hbar_constructor_rejects_invalid_types(value: object) -> None:
    """The constructor must not silently coerce unsupported input types."""
    with pytest.raises(TypeError):
        Hbar(value)
