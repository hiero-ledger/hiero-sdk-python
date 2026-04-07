from __future__ import annotations

from decimal import Decimal

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from hiero_sdk_python import AccountId, HbarUnit, PrivateKey, TransactionId, TransferTransaction
from tests.fuzz.support.classes import HbarConstructorCase, HbarStringCase


def sized_hex(byte_length: int) -> SearchStrategy[str]:
    """Return a fixed-length hex string strategy."""
    return st.binary(min_size=byte_length, max_size=byte_length).map(bytes.hex)


def with_optional_0x(hex_strategy: SearchStrategy[str]) -> SearchStrategy[str]:
    """Allow a hex string with or without the `0x` prefix."""
    return st.one_of(hex_strategy, hex_strategy.map(lambda value: f"0x{value}"))


def decimal_string(value: Decimal) -> str:
    """Format a Decimal without trailing zeros."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def hbar_string_case(unit: HbarUnit, tinybars: int) -> HbarStringCase:
    """Build a valid Hbar string case from an exact tinybar amount."""
    amount = Decimal(tinybars) / Decimal(unit.tinybar)
    if unit == HbarUnit.HBAR:
        return HbarStringCase(text=decimal_string(amount), tinybars=tinybars)
    return HbarStringCase(text=f"{decimal_string(amount)} {unit.symbol}", tinybars=tinybars)


def hbar_constructor_case(unit: HbarUnit, tinybars: int) -> HbarConstructorCase:
    """Build a valid Hbar constructor case from an exact tinybar amount."""
    if unit == HbarUnit.TINYBAR:
        amount: int | float | Decimal = tinybars
    else:
        amount = Decimal(tinybars) / Decimal(unit.tinybar)
    return HbarConstructorCase(amount=amount, unit=unit, tinybars=tinybars)


def build_valid_transaction_bytes() -> tuple[bytes, bytes]:
    """Build one valid unsigned and one valid signed transaction payload."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    tx = TransferTransaction().add_hbar_transfer(operator_id, -100_000_000).add_hbar_transfer(receiver_id, 100_000_000)
    tx.transaction_id = TransactionId.generate(operator_id)
    tx.node_account_id = node_id
    tx.freeze()
    unsigned_bytes = tx.to_bytes()

    signed_tx = TransferTransaction.from_bytes(unsigned_bytes)
    signed_tx.sign(PrivateKey.from_string_ed25519("02" * 32))
    signed_bytes = signed_tx.to_bytes()
    return unsigned_bytes, signed_bytes
