from __future__ import annotations

import pytest
from hypothesis import given, settings

from hiero_sdk_python import Transaction
from tests.fuzz.conftest import get_strategy


pytestmark = pytest.mark.fuzz


@settings(max_examples=80)
@given(data=get_strategy("tx_valid_bytes"))
def test_transaction_from_bytes_roundtrips_valid_payloads(data: bytes) -> None:
    """Serialized transactions must deserialize and reserialize byte-for-byte."""
    parsed = Transaction.from_bytes(data)
    reparsed = Transaction.from_bytes(parsed.to_bytes())

    assert parsed.to_bytes() == data
    assert type(reparsed) is type(parsed)
    assert reparsed.to_bytes() == parsed.to_bytes()


@settings(max_examples=30)
@given(data=get_strategy("tx_invalid_empty"))
def test_transaction_from_bytes_rejects_empty_payloads(data: bytes) -> None:
    """Empty payloads are explicitly invalid for Transaction.from_bytes()."""
    with pytest.raises(ValueError):
        Transaction.from_bytes(data)


@settings(max_examples=80)
@given(data=get_strategy("tx_invalid_truncated"))
def test_transaction_from_bytes_rejects_truncated_payloads(data: bytes) -> None:
    """Truncated transaction payloads must raise ValueError."""
    with pytest.raises(ValueError):
        Transaction.from_bytes(data)


@settings(max_examples=80)
@given(data=get_strategy("tx_invalid_corrupted"))
def test_transaction_from_bytes_rejects_corrupted_payloads(data: bytes) -> None:
    """Byte-level corruption of a valid payload must not deserialize successfully."""
    with pytest.raises(ValueError):
        Transaction.from_bytes(data)


@settings(max_examples=80)
@given(data=get_strategy("tx_invalid_random"))
def test_transaction_from_bytes_rejects_random_payloads(data: bytes) -> None:
    """Random byte payloads must not parse as valid SDK transactions."""
    with pytest.raises(ValueError):
        Transaction.from_bytes(data)
