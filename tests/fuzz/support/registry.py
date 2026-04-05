import string
from decimal import Decimal
from typing import Any, NamedTuple

import pytest
from eth_abi.exceptions import EncodingTypeError, ValueOutOfBounds
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from hiero_sdk_python import HbarUnit, PrivateKey
from tests.fuzz.support.classes import (
    AccountIdAliasCase,
    ContractValueCase,
    EntityIdCase,
    InvalidContractValueCase,
)
from tests.fuzz.support.helpers import (
    build_valid_transaction_bytes,
    hbar_constructor_case,
    hbar_string_case,
    sized_hex,
    with_optional_0x,
)

MAX_I64 = 2**63 - 1
MIN_I64 = -(2**63)


class _IdentifierPrimitives(NamedTuple):
    """Shared scalar strategies reused by the identifier-related builders."""

    shard: SearchStrategy[int]
    realm: SearchStrategy[int]
    entity_num: SearchStrategy[int]
    checksum: SearchStrategy[str]


class _KeySampleValues(NamedTuple):
    """Precomputed valid key encodings reused across identifier and key strategies."""

    ed_private_raw: str
    ecdsa_private_raw: str
    ed_private_der: str
    ecdsa_private_der: str
    ed_public_raw: str
    ecdsa_public_compressed: str
    ecdsa_public_uncompressed: str
    ed_public_der: str
    ecdsa_public_der: str
    ed25519_alias_hex: str
    ecdsa_alias_hex: str
    evm_hex: str


def _build_identifier_primitives() -> _IdentifierPrimitives:
    """Build the shared scalar strategies used to compose Hedera-style identifiers."""
    return _IdentifierPrimitives(
        shard=st.integers(min_value=0, max_value=4096),
        realm=st.integers(min_value=0, max_value=4096),
        entity_num=st.integers(min_value=0, max_value=MAX_I64),
        checksum=st.text(alphabet=string.ascii_lowercase, min_size=5, max_size=5),
    )


def _build_key_sample_values() -> _KeySampleValues:
    """Build canonical valid key samples once so all dependent strategies stay consistent."""
    ed_private_raw = "01" * 32
    ecdsa_private_raw = "00" * 31 + "01"

    ed_private_key = PrivateKey.from_string_ed25519(ed_private_raw)
    ecdsa_private_key = PrivateKey.from_string_ecdsa(ecdsa_private_raw)
    ed_public_key = ed_private_key.public_key()
    ecdsa_public_key = ecdsa_private_key.public_key()

    return _KeySampleValues(
        ed_private_raw=ed_private_raw,
        ecdsa_private_raw=ecdsa_private_raw,
        ed_private_der=ed_private_key.to_bytes_der().hex(),
        ecdsa_private_der=ecdsa_private_key.to_bytes_der().hex(),
        ed_public_raw=ed_public_key.to_bytes_raw().hex(),
        ecdsa_public_compressed=ecdsa_public_key.to_bytes_ecdsa().hex(),
        ecdsa_public_uncompressed=ecdsa_public_key.to_bytes_ecdsa(compressed=False).hex(),
        ed_public_der=ed_public_key.to_bytes_der().hex(),
        ecdsa_public_der=ecdsa_public_key.to_bytes_der().hex(),
        ed25519_alias_hex=ed_public_key.to_bytes_raw().hex(),
        ecdsa_alias_hex=ecdsa_public_key.to_bytes_ecdsa().hex(),
        evm_hex="abcdef0123456789abcdef0123456789abcdef01",
    )


def _build_entity_id_strategies(
    primitives: _IdentifierPrimitives,
) -> dict[str, SearchStrategy[Any]]:
    """Build valid dotted and checksum entity ID strategies with the current numeric bounds."""
    entity_id_valid_dotted = st.builds(
        lambda shard_value, realm_value, num_value: EntityIdCase(
            text=f"{shard_value}.{realm_value}.{num_value}",
            shard=shard_value,
            realm=realm_value,
            value=num_value,
        ),
        primitives.shard,
        primitives.realm,
        primitives.entity_num,
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
        primitives.checksum,
    )

    return {
        "entity_id_valid_dotted": entity_id_valid_dotted,
        "entity_id_valid_checksum": entity_id_valid_checksum,
    }


def _build_alias_identifier_strategies(
    primitives: _IdentifierPrimitives, key_samples: _KeySampleValues
) -> dict[str, SearchStrategy[Any]]:
    """Build valid account and contract alias strategies using canonical alias and EVM samples."""
    ed25519_alias_hex = st.just(key_samples.ed25519_alias_hex)
    ecdsa_alias_hex = st.just(key_samples.ecdsa_alias_hex)
    evm_hex = st.just(key_samples.evm_hex)

    account_id_valid_alias = st.builds(
        lambda shard_value, realm_value, alias_hex: AccountIdAliasCase(
            text=f"{shard_value}.{realm_value}.{alias_hex}",
            shard=shard_value,
            realm=realm_value,
            alias_hex=alias_hex,
        ),
        primitives.shard,
        primitives.realm,
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
            primitives.shard,
            primitives.realm,
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
        primitives.shard,
        primitives.realm,
        evm_hex,
    )

    return {
        "account_id_valid_alias": account_id_valid_alias,
        "account_id_valid_evm": account_id_valid_evm,
        "contract_id_valid_evm": contract_id_valid_evm,
    }


def _build_invalid_identifier_strategies() -> dict[str, SearchStrategy[Any]]:
    """Build malformed identifier strategies while preserving existing invalid-string coverage."""
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

    return {
        "account_id_invalid_string": invalid_account_strings,
        "token_id_invalid_string": invalid_token_strings,
        "contract_id_invalid_string": invalid_contract_strings,
        "entity_id_invalid_type": entity_id_invalid_type,
    }


def _build_private_key_strategies(key_samples: _KeySampleValues) -> dict[str, SearchStrategy[Any]]:
    """Build the private key strategies from the canonical valid sample encodings."""
    private_key_valid_string = st.one_of(
        with_optional_0x(st.sampled_from([key_samples.ed_private_raw, key_samples.ed_private_der])),
    )
    private_key_valid_bytes = st.sampled_from(
        [
            bytes.fromhex(key_samples.ed_private_raw),
            bytes.fromhex(key_samples.ed_private_der),
            bytes.fromhex(key_samples.ecdsa_private_der),
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

    return {
        "private_key_valid_string": private_key_valid_string,
        "private_key_valid_bytes": private_key_valid_bytes,
        "private_key_invalid_string": private_key_invalid_string,
        "private_key_invalid_bytes": private_key_invalid_bytes,
    }


def _build_public_key_strategies(key_samples: _KeySampleValues) -> dict[str, SearchStrategy[Any]]:
    """Build the public key strategies from the canonical valid sample encodings."""
    public_key_valid_string = st.one_of(
        with_optional_0x(
            st.sampled_from(
                [
                    key_samples.ed_public_raw,
                    key_samples.ecdsa_public_compressed,
                    key_samples.ecdsa_public_uncompressed,
                    key_samples.ed_public_der,
                    key_samples.ecdsa_public_der,
                ]
            )
        ),
    )
    public_key_valid_bytes = st.sampled_from(
        [
            bytes.fromhex(key_samples.ed_public_raw),
            bytes.fromhex(key_samples.ecdsa_public_compressed),
            bytes.fromhex(key_samples.ecdsa_public_uncompressed),
            bytes.fromhex(key_samples.ed_public_der),
            bytes.fromhex(key_samples.ecdsa_public_der),
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

    return {
        "public_key_valid_string": public_key_valid_string,
        "public_key_valid_bytes": public_key_valid_bytes,
        "public_key_invalid_string": public_key_invalid_string,
        "public_key_invalid_bytes": public_key_invalid_bytes,
    }


def _build_key_strategies(key_samples: _KeySampleValues) -> dict[str, SearchStrategy[Any]]:
    """Build the complete private and public key strategy registry entries."""
    strategies: dict[str, SearchStrategy[Any]] = {}
    strategies.update(_build_private_key_strategies(key_samples))
    strategies.update(_build_public_key_strategies(key_samples))
    return strategies


def _build_hbar_strategies() -> dict[str, SearchStrategy[Any]]:
    """Build Hbar parsing and constructor strategies, including intentional invalid edge cases."""
    hbar_valid_tinybars = st.integers(min_value=-(10**12), max_value=10**12)
    hbar_valid_string = st.one_of(
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.HBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.MICROBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.MILLIBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.KILOBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.MEGABAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_string_case(HbarUnit.GIGABAR, tinybars)),
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
        hbar_valid_tinybars.map(lambda tinybars: hbar_constructor_case(HbarUnit.TINYBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_constructor_case(HbarUnit.HBAR, tinybars)),
        hbar_valid_tinybars.map(lambda tinybars: hbar_constructor_case(HbarUnit.MICROBAR, tinybars)),
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

    return {
        "hbar_valid_string": hbar_valid_string,
        "hbar_invalid_string": hbar_invalid_string,
        "hbar_valid_constructor": hbar_valid_constructor,
        "hbar_invalid_nonfinite_float": hbar_invalid_nonfinite_float,
        "fractional_tinybar_amount": fractional_tinybar_amount,
        "hbar_invalid_constructor_type": hbar_invalid_constructor_type,
    }


def _build_transaction_byte_strategies() -> dict[str, SearchStrategy[Any]]:
    """Build valid and intentionally broken transaction byte payload strategies."""
    unsigned_tx_bytes, signed_tx_bytes = build_valid_transaction_bytes()
    tx_valid_bytes = st.sampled_from([unsigned_tx_bytes, signed_tx_bytes])
    tx_invalid_empty = st.just(b"")
    tx_invalid_random = st.binary(min_size=1, max_size=8)
    tx_invalid_truncated = st.sampled_from(
        [unsigned_tx_bytes[:10], signed_tx_bytes[:10], unsigned_tx_bytes[:-1], signed_tx_bytes[:-1]]
    )
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

    return {
        "tx_valid_bytes": tx_valid_bytes,
        "tx_invalid_empty": tx_invalid_empty,
        "tx_invalid_random": tx_invalid_random,
        "tx_invalid_truncated": tx_invalid_truncated,
        "tx_invalid_corrupted": tx_invalid_corrupted,
    }


def _build_contract_value_strategies() -> dict[str, SearchStrategy[Any]]:
    """Build valid and invalid contract parameter cases without changing ABI edge coverage."""
    valid_contract_value = st.one_of(
        st.booleans().map(lambda value: ContractValueCase("add_bool", value)),
        st.integers(min_value=-(2**31), max_value=2**31 - 1).map(lambda value: ContractValueCase("add_int32", value)),
        st.integers(min_value=0, max_value=2**32 - 1).map(lambda value: ContractValueCase("add_uint32", value)),
        st.integers(min_value=MIN_I64, max_value=MAX_I64).map(lambda value: ContractValueCase("add_int64", value)),
        st.integers(min_value=0, max_value=2**64 - 1).map(lambda value: ContractValueCase("add_uint64", value)),
        st.integers(min_value=-(2**255), max_value=2**255 - 1).map(
            lambda value: ContractValueCase("add_int256", value)
        ),
        st.integers(min_value=0, max_value=2**256 - 1).map(lambda value: ContractValueCase("add_uint256", value)),
        st.text(min_size=0, max_size=32).map(lambda value: ContractValueCase("add_string", value)),
        st.binary(min_size=0, max_size=64).map(lambda value: ContractValueCase("add_bytes", value)),
        st.binary(min_size=0, max_size=32).map(lambda value: ContractValueCase("add_bytes32", value)),
        st.binary(min_size=20, max_size=20).map(lambda value: ContractValueCase("add_address", value)),
        with_optional_0x(sized_hex(20)).map(lambda value: ContractValueCase("add_address", value)),
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
        "contract_value_valid": valid_contract_value,
        "contract_value_invalid": invalid_contract_value,
        "contract_function_name": contract_function_name,
    }


def build_strategy_registry() -> dict[str, SearchStrategy[Any]]:
    """Assemble all domain-specific strategy groups into the shared fuzz registry."""
    primitives = _build_identifier_primitives()
    key_samples = _build_key_sample_values()

    registry: dict[str, SearchStrategy[Any]] = {}
    registry.update(_build_entity_id_strategies(primitives))
    registry.update(_build_alias_identifier_strategies(primitives, key_samples))
    registry.update(_build_invalid_identifier_strategies())
    registry.update(_build_key_strategies(key_samples))
    registry.update(_build_hbar_strategies())
    registry.update(_build_transaction_byte_strategies())
    registry.update(_build_contract_value_strategies())
    return registry


FUZZ_STRATEGIES = build_strategy_registry()


def get_strategy(name: str) -> SearchStrategy[Any]:
    """Return the named fuzz strategy from the shared registry or raise a helpful KeyError."""
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
