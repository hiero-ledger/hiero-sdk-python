"""Shared Hypothesis profiles, fixtures, and strict fuzz strategies."""

from __future__ import annotations

import os
import string
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
from eth_abi.exceptions import EncodingTypeError, ValueOutOfBounds
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from hiero_sdk_python import (
    AccountId,
    HbarUnit,
    PrivateKey,
    TransactionId,
    TransferTransaction,
)

MAX_I64 = 2**63 - 1
MIN_I64 = -(2**63)


@dataclass(frozen=True)
class EntityIdCase:
    """A parsed entity ID expectation for public string parsers."""

    text: str
    shard: int
    realm: int
    value: int
    checksum: str | None = None


@dataclass(frozen=True)
class AccountIdAliasCase:
    """A valid account alias or EVM-address input."""

    text: str
    shard: int
    realm: int
    alias_hex: str | None = None
    evm_hex: str | None = None


@dataclass(frozen=True)
class HbarStringCase:
    """A valid public Hbar string and its exact tinybar value."""

    text: str
    tinybars: int


@dataclass(frozen=True)
class HbarConstructorCase:
    """A valid Hbar constructor input and its exact tinybar value."""

    amount: int | float | Decimal
    unit: HbarUnit
    tinybars: int


@dataclass(frozen=True)
class ContractValueCase:
    """A valid contract parameter case routed to an explicit public add_* method."""

    method_name: str
    value: Any


@dataclass(frozen=True)
class InvalidContractValueCase:
    """An invalid contract parameter case with a precise expected exception."""

    method_name: str
    value: Any
    expected_exception: type[BaseException]


def _load_hypothesis_profile() -> None:
    """
    Following https://docs.github.com/en/actions/reference/workflows-and-actions/variables
    CI variable is always  set to True in github actions.
    """
    settings.register_profile(
        "ci",
        settings(
            derandomize=True,
            max_examples=300,
            deadline=750,
            suppress_health_check=[HealthCheck.too_slow],
        ),
    )
    settings.register_profile(
        "local",
        settings(
            derandomize=False,
            max_examples=1000,
            deadline=None,
        ),
    )

    requested = os.getenv("HYPOTHESIS_PROFILE")
    if requested:
        settings.load_profile(requested)
        return

    settings.load_profile("ci" if os.getenv("CI") else "local") #  https://docs.github.com/en/actions/reference/workflows-and-actions/variables


def _sized_hex(byte_length: int) -> SearchStrategy[str]:
    return st.binary(min_size=byte_length, max_size=byte_length).map(bytes.hex)


def _with_optional_0x(hex_strategy: SearchStrategy[str]) -> SearchStrategy[str]:
    return st.one_of(hex_strategy, hex_strategy.map(lambda value: f"0x{value}"))


def _decimal_string(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _hbar_string_case(unit: HbarUnit, tinybars: int) -> HbarStringCase:
    amount = Decimal(tinybars) / Decimal(unit.tinybar)
    if unit == HbarUnit.HBAR:
        return HbarStringCase(text=_decimal_string(amount), tinybars=tinybars)
    return HbarStringCase(text=f"{_decimal_string(amount)} {unit.symbol}", tinybars=tinybars)


def _hbar_constructor_case(unit: HbarUnit, tinybars: int) -> HbarConstructorCase:
    if unit == HbarUnit.TINYBAR:
        amount: int | float | Decimal = tinybars
    else:
        amount = Decimal(tinybars) / Decimal(unit.tinybar)
    return HbarConstructorCase(amount=amount, unit=unit, tinybars=tinybars)


def _build_valid_transaction_bytes() -> tuple[bytes, bytes]:
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    tx = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )
    tx.transaction_id = TransactionId.generate(operator_id)
    tx.node_account_id = node_id
    tx.freeze()
    unsigned_bytes = tx.to_bytes()

    signed_tx = TransferTransaction.from_bytes(unsigned_bytes)
    signed_tx.sign(PrivateKey.from_string_ed25519("02" * 32))
    signed_bytes = signed_tx.to_bytes()
    return unsigned_bytes, signed_bytes


def _build_strategy_registry() -> dict[str, SearchStrategy[Any]]:
    shard = st.integers(min_value=0, max_value=4096)
    realm = st.integers(min_value=0, max_value=4096)
    entity_num = st.integers(min_value=0, max_value=MAX_I64)
    checksum = st.text(alphabet=string.ascii_lowercase, min_size=5, max_size=5)

    entity_id_valid_dotted = st.builds(
        lambda shard_value, realm_value, num_value: EntityIdCase(
            text=f"{shard_value}.{realm_value}.{num_value}",
            shard=shard_value,
            realm=realm_value,
            value=num_value,
        ),
        shard,
        realm,
        entity_num,
    )
    entity_id_valid_checksum = st.builds(
        lambda base, checksum_value: EntityIdCase(
            text=f"{base.shard}.{base.realm}.{base.value}-{checksum_value}",
            shard=base.shard,
            realm=base.realm,
            value=base.value,
            checksum=checksum_value,
        ),
        entity_id_valid_dotted,
        checksum,
    )

    ed25519_alias_hex = st.just(
        PrivateKey.from_string_ed25519("01" * 32).public_key().to_bytes_raw().hex()
    )
    ecdsa_alias_hex = st.just(
        PrivateKey.from_string_ecdsa("00" * 31 + "01").public_key().to_bytes_ecdsa().hex()
    )
    evm_hex = st.just("abcdef0123456789abcdef0123456789abcdef01")

    account_id_valid_alias = st.builds(
        lambda shard_value, realm_value, alias_hex: AccountIdAliasCase(
            text=f"{shard_value}.{realm_value}.{alias_hex}",
            shard=shard_value,
            realm=realm_value,
            alias_hex=alias_hex,
        ),
        shard,
        realm,
        st.one_of(ed25519_alias_hex, ecdsa_alias_hex),
    )
    account_id_valid_evm = st.one_of(
        evm_hex.map(lambda value: AccountIdAliasCase(text=value, shard=0, realm=0, evm_hex=value)),
        evm_hex.map(lambda value: AccountIdAliasCase(text=f"0x{value}", shard=0, realm=0, evm_hex=value)),
        st.builds(
            lambda shard_value, realm_value, value: AccountIdAliasCase(
                text=f"{shard_value}.{realm_value}.{value}",
                shard=shard_value,
                realm=realm_value,
                evm_hex=value,
            ),
            shard,
            realm,
            evm_hex,
        ),
    )

    contract_id_valid_evm = st.builds(
        lambda shard_value, realm_value, value: AccountIdAliasCase(
            text=f"{shard_value}.{realm_value}.{value}",
            shard=shard_value,
            realm=realm_value,
            evm_hex=value,
        ),
        shard,
        realm,
        evm_hex,
    )

    invalid_entity_strings = st.one_of(
        st.sampled_from(
            [
                "",
                ".",
                "..",
                "0",
                "0.0",
                "0.0.0.0",
                "0_0_0",
                "0/0/0",
                "0.0.-1",
                "-1.0.0",
                "0.-1.0",
                "abc.def.ghi",
                "1e3",
                "nan",
                "inf",
            ]
        ),
        st.text(alphabet=string.ascii_letters + "_-:/ ", min_size=1, max_size=48),
    )
    invalid_account_strings = st.one_of(
        invalid_entity_strings,
        st.sampled_from(
            [
                "0.0.0xabcdef0123456789abcdef0123456789abcdef01",
                "0x1234",
                "abcdef",
            ]
        ),
    )
    invalid_contract_strings = st.one_of(
        invalid_entity_strings,
        st.sampled_from(
            [
                "abcdef0123456789abcdef0123456789abcdef01",
                "0xabcdef0123456789abcdef0123456789abcdef01",
                "1.2.0xabcdef0123456789abcdef0123456789abcdef01",
            ]
        ),
    )
    invalid_token_strings = st.one_of(
        invalid_entity_strings,
        st.sampled_from(
            [
                "abcdef0123456789abcdef0123456789abcdef01",
                "0xabcdef0123456789abcdef0123456789abcdef01",
                "1.2.abcdef0123456789abcdef0123456789abcdef01",
            ]
        ),
    )

    entity_id_invalid_type = st.sampled_from([None, 123, True, {}, []])

    ed_private_raw = "01" * 32
    ecdsa_private_raw = "00" * 31 + "01"
    ed_private_der = PrivateKey.from_string_ed25519(ed_private_raw).to_bytes_der().hex()
    ecdsa_private_der = PrivateKey.from_string_ecdsa(ecdsa_private_raw).to_bytes_der().hex()
    ed_public_raw = PrivateKey.from_string_ed25519(ed_private_raw).public_key().to_bytes_raw().hex()
    ecdsa_public_compressed = (
        PrivateKey.from_string_ecdsa(ecdsa_private_raw).public_key().to_bytes_ecdsa().hex()
    )
    ecdsa_public_uncompressed = (
        PrivateKey.from_string_ecdsa(ecdsa_private_raw).public_key().to_bytes_ecdsa(compressed=False).hex()
    )
    ed_public_der = PrivateKey.from_string_ed25519(ed_private_raw).public_key().to_bytes_der().hex()
    ecdsa_public_der = PrivateKey.from_string_ecdsa(ecdsa_private_raw).public_key().to_bytes_der().hex()

    private_key_valid_string = st.one_of(
        _with_optional_0x(st.sampled_from([ed_private_raw, ed_private_der])),
    )
    private_key_valid_bytes = st.sampled_from(
        [
            bytes.fromhex(ed_private_raw),
            bytes.fromhex(ed_private_der),
            bytes.fromhex(ecdsa_private_der),
        ]
    )
    private_key_invalid_string = st.one_of(
        st.sampled_from(
            [
                "not-hex",
                "xyz",
                "0xzz",
                "11" * 31,
                "11" * 33,
                "30",
            ]
        ),
        st.text(alphabet="ghijklmnopqrstuvwxyz_-", min_size=1, max_size=66),
    )
    private_key_invalid_bytes = st.one_of(
        st.binary(min_size=0, max_size=31),
        st.binary(min_size=33, max_size=96),
        st.binary(min_size=32, max_size=64).map(lambda data: b"\x30" + data),
    )

    public_key_valid_string = st.one_of(
        _with_optional_0x(st.sampled_from([ed_public_raw, ecdsa_public_compressed, ecdsa_public_uncompressed, ed_public_der, ecdsa_public_der])),
    )
    public_key_valid_bytes = st.sampled_from(
        [
            bytes.fromhex(ed_public_raw),
            bytes.fromhex(ecdsa_public_compressed),
            bytes.fromhex(ecdsa_public_uncompressed),
            bytes.fromhex(ed_public_der),
            bytes.fromhex(ecdsa_public_der),
        ]
    )
    public_key_invalid_string = st.one_of(
        st.sampled_from(
            [
                "not-hex",
                "0xzz",
                "05" + "00" * 32,
                "11" * 31,
                "11" * 34,
                "30",
            ]
        ),
        st.text(alphabet="ghijklmnopqrstuvwxyz_-", min_size=1, max_size=130),
    )
    public_key_invalid_bytes = st.one_of(
        st.binary(min_size=0, max_size=31),
        st.just(bytes.fromhex("05" + "00" * 32)),
        st.binary(min_size=34, max_size=64),
        st.binary(min_size=32, max_size=64).map(lambda data: b"\x30" + data),
    )

    hbar_valid_tinybars = st.integers(min_value=-(10**18), max_value=10**18)
    hbar_valid_string = st.one_of(
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.HBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.MICROBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.MILLIBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.KILOBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.MEGABAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_string_case(HbarUnit.GIGABAR, tinybars)),
    )
    hbar_invalid_string = st.one_of(
        st.sampled_from(
            [
                "1e3",
                "1 hbar",
                "1 tinybar",
                "1 tℏ",
                "1.5 tℏ",
                " 1 ℏ",
                "1  ℏ",
                "1\tℏ",
                "nan",
                "inf",
                "-inf",
                "",
            ]
        ),
        st.text(alphabet=string.ascii_letters + "_-", min_size=1, max_size=24),
    )
    hbar_valid_constructor = st.one_of(
        hbar_valid_tinybars.map(lambda tinybars: _hbar_constructor_case(HbarUnit.TINYBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_constructor_case(HbarUnit.HBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: _hbar_constructor_case(HbarUnit.MICROBAR, tinybars)),
    )
    hbar_invalid_nonfinite_float = st.sampled_from([float("inf"), float("-inf"), float("nan")])
    fractional_tinybar_amount = st.decimals(
        min_value=Decimal("-1000"),
        max_value=Decimal("1000"),
        allow_nan=False,
        allow_infinity=False,
        places=1,
    ).filter(lambda value: value != value.to_integral_value())
    hbar_invalid_constructor_type = st.sampled_from(["1", None, True, object()])

    unsigned_tx_bytes, signed_tx_bytes = _build_valid_transaction_bytes()
    tx_valid_bytes = st.sampled_from([unsigned_tx_bytes, signed_tx_bytes])
    tx_invalid_empty = st.just(b"")
    tx_invalid_random = st.binary(min_size=1, max_size=8)
    tx_invalid_truncated = st.sampled_from([unsigned_tx_bytes[:10], signed_tx_bytes[:10], unsigned_tx_bytes[:-1], signed_tx_bytes[:-1]])
    tx_invalid_corrupted = st.sampled_from(
        [
            bytes([unsigned_tx_bytes[0] ^ 0x01]) + unsigned_tx_bytes[1:],
            unsigned_tx_bytes[:1] + bytes([unsigned_tx_bytes[1] ^ 0x01]) + unsigned_tx_bytes[2:],
            unsigned_tx_bytes[:20] + b"\x00" + unsigned_tx_bytes[20:],
            b"\x00" + unsigned_tx_bytes,
            unsigned_tx_bytes + b"\x00",
            bytes([signed_tx_bytes[0] ^ 0x01]) + signed_tx_bytes[1:],
            signed_tx_bytes[:1] + bytes([signed_tx_bytes[1] ^ 0x01]) + signed_tx_bytes[2:],
            signed_tx_bytes[:20] + b"\x00" + signed_tx_bytes[20:],
            b"\x00" + signed_tx_bytes,
            signed_tx_bytes + b"\x00",
        ]
    )

    valid_contract_value = st.one_of(
        st.booleans().map(lambda value: ContractValueCase("add_bool", value)),
        st.integers(min_value=-(2**31), max_value=2**31 - 1).map(lambda value: ContractValueCase("add_int32", value)),
        st.integers(min_value=0, max_value=2**32 - 1).map(lambda value: ContractValueCase("add_uint32", value)),
        st.integers(min_value=MIN_I64, max_value=MAX_I64).map(lambda value: ContractValueCase("add_int64", value)),
        st.integers(min_value=0, max_value=2**64 - 1).map(lambda value: ContractValueCase("add_uint64", value)),
        st.integers(min_value=-(2**255), max_value=2**255 - 1).map(lambda value: ContractValueCase("add_int256", value)),
        st.integers(min_value=0, max_value=2**256 - 1).map(lambda value: ContractValueCase("add_uint256", value)),
        st.text(min_size=0, max_size=32).map(lambda value: ContractValueCase("add_string", value)),
        st.binary(min_size=0, max_size=64).map(lambda value: ContractValueCase("add_bytes", value)),
        st.binary(min_size=0, max_size=32).map(lambda value: ContractValueCase("add_bytes32", value)),
        st.binary(min_size=20, max_size=20).map(lambda value: ContractValueCase("add_address", value)),
        _with_optional_0x(st.just("abcdef0123456789abcdef0123456789abcdef01")).map(
            lambda value: ContractValueCase("add_address", value)
        ),
        st.lists(st.integers(min_value=-(2**31), max_value=2**31 - 1), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_int32_array", value)
        ),
        st.lists(st.integers(min_value=0, max_value=2**32 - 1), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_uint32_array", value)
        ),
        st.lists(st.binary(min_size=0, max_size=24), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_bytes_array", value)
        ),
        st.lists(st.binary(min_size=0, max_size=32), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_bytes32_array", value)
        ),
        st.lists(st.text(min_size=0, max_size=16), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_string_array", value)
        ),
        st.lists(st.binary(min_size=20, max_size=20), min_size=0, max_size=6).map(
            lambda value: ContractValueCase("add_address_array", value)
        ),
    )
    invalid_contract_value = st.one_of(
        st.just(InvalidContractValueCase("add_bool", "true", EncodingTypeError)),
        st.just(InvalidContractValueCase("add_int32", 2**31, ValueOutOfBounds)),
        st.just(InvalidContractValueCase("add_uint32", -1, ValueOutOfBounds)),
        st.just(InvalidContractValueCase("add_bytes32", b"a" * 33, ValueOutOfBounds)),
        st.just(InvalidContractValueCase("add_address", b"a" * 19, EncodingTypeError)),
        st.just(InvalidContractValueCase("add_address", "0x1234", EncodingTypeError)),
        st.just(InvalidContractValueCase("add_bytes_array", [b"a", "b"], EncodingTypeError)),
        st.just(InvalidContractValueCase("add_string_array", ["ok", b"bad"], EncodingTypeError)),
        st.just(InvalidContractValueCase("add_address_array", [b"a" * 19], EncodingTypeError)),
    )
    contract_function_name = st.one_of(
        st.none(),
        st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=24),
    )

    return {
        "entity_id_valid_dotted": entity_id_valid_dotted,
        "entity_id_valid_checksum": entity_id_valid_checksum,
        "account_id_valid_alias": account_id_valid_alias,
        "account_id_valid_evm": account_id_valid_evm,
        "contract_id_valid_evm": contract_id_valid_evm,
        "account_id_invalid_string": invalid_account_strings,
        "token_id_invalid_string": invalid_token_strings,
        "contract_id_invalid_string": invalid_contract_strings,
        "entity_id_invalid_type": entity_id_invalid_type,
        "private_key_valid_string": private_key_valid_string,
        "private_key_valid_bytes": private_key_valid_bytes,
        "private_key_invalid_string": private_key_invalid_string,
        "private_key_invalid_bytes": private_key_invalid_bytes,
        "public_key_valid_string": public_key_valid_string,
        "public_key_valid_bytes": public_key_valid_bytes,
        "public_key_invalid_string": public_key_invalid_string,
        "public_key_invalid_bytes": public_key_invalid_bytes,
        "hbar_valid_string": hbar_valid_string,
        "hbar_invalid_string": hbar_invalid_string,
        "hbar_valid_constructor": hbar_valid_constructor,
        "hbar_invalid_nonfinite_float": hbar_invalid_nonfinite_float,
        "fractional_tinybar_amount": fractional_tinybar_amount,
        "hbar_invalid_constructor_type": hbar_invalid_constructor_type,
        "tx_valid_bytes": tx_valid_bytes,
        "tx_invalid_empty": tx_invalid_empty,
        "tx_invalid_random": tx_invalid_random,
        "tx_invalid_truncated": tx_invalid_truncated,
        "tx_invalid_corrupted": tx_invalid_corrupted,
        "contract_value_valid": valid_contract_value,
        "contract_value_invalid": invalid_contract_value,
        "contract_function_name": contract_function_name,
    }


_load_hypothesis_profile()
FUZZ_STRATEGIES = _build_strategy_registry()


def get_strategy(name: str) -> SearchStrategy[Any]:
    """Return a named fuzz strategy."""
    try:
        return FUZZ_STRATEGIES[name]
    except KeyError as exc:
        available = ", ".join(sorted(FUZZ_STRATEGIES))
        raise KeyError(f"Unknown strategy {name!r}. Available strategies: {available}") from exc


@pytest.fixture(name="fuzz_strategies")
def fuzz_strategies_fixture() -> dict[str, SearchStrategy[Any]]:
    """Provide the shared fuzz strategy registry."""
    return FUZZ_STRATEGIES


@pytest.fixture(name="get_strategy")
def get_strategy_fixture() -> Any:
    """Provide the named strategy accessor."""
    return get_strategy


__all__ = [
    "AccountIdAliasCase",
    "ContractValueCase",
    "EntityIdCase",
    "FUZZ_STRATEGIES",
    "HbarConstructorCase",
    "HbarStringCase",
    "InvalidContractValueCase",
    "get_strategy",
]
