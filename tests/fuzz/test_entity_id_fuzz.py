import warnings

import pytest
from hypothesis import given

from hiero_sdk_python import AccountId, TokenId
from hiero_sdk_python.contract.contract_id import ContractId
from tests.fuzz.conftest import AccountIdAliasCase, EntityIdCase, get_strategy

pytestmark = pytest.mark.fuzz


def _assert_account_roundtrip(case: EntityIdCase) -> None:
    parsed = AccountId.from_string(case.text)
    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.num == case.value
    assert parsed.checksum == case.checksum
    assert str(parsed) == f"{case.shard}.{case.realm}.{case.value}"
    canonical = AccountId.from_string(str(parsed))
    assert canonical.shard == parsed.shard
    assert canonical.realm == parsed.realm
    assert canonical.num == parsed.num
    assert canonical.alias_key == parsed.alias_key
    assert canonical.evm_address == parsed.evm_address
    assert canonical.checksum is None


def _assert_token_roundtrip(case: EntityIdCase) -> None:
    parsed = TokenId.from_string(case.text)
    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.num == case.value
    assert parsed.checksum == case.checksum
    assert str(parsed) == f"{case.shard}.{case.realm}.{case.value}"
    canonical = TokenId.from_string(str(parsed))
    assert canonical.shard == parsed.shard
    assert canonical.realm == parsed.realm
    assert canonical.num == parsed.num
    assert canonical.checksum is None


def _assert_contract_roundtrip(case: EntityIdCase) -> None:
    parsed = ContractId.from_string(case.text)
    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.contract == case.value
    assert parsed.checksum == case.checksum
    assert str(parsed) == f"{case.shard}.{case.realm}.{case.value}"
    canonical = ContractId.from_string(str(parsed))
    assert canonical.shard == parsed.shard
    assert canonical.realm == parsed.realm
    assert canonical.contract == parsed.contract
    assert canonical.checksum is None


@given(case=get_strategy("entity_id_valid_dotted"))
def test_account_id_accepts_valid_dotted_ids(case: EntityIdCase) -> None:
    """Valid dotted account IDs must parse and round-trip canonically."""
    _assert_account_roundtrip(case)


@given(case=get_strategy("entity_id_valid_checksum"))
def test_account_id_preserves_checksum_text(case: EntityIdCase) -> None:
    """Checksum-bearing account IDs must retain checksum metadata after parsing."""
    _assert_account_roundtrip(case)


@given(case=get_strategy("account_id_valid_alias"))
def test_account_id_accepts_valid_alias_hex(case: AccountIdAliasCase) -> None:
    """Alias-style account IDs must decode into alias_key and reserialize canonically."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = AccountId.from_string(case.text)

    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.num == 0
    assert parsed.alias_key is not None
    assert parsed.evm_address is None
    assert parsed.alias_key.to_bytes_raw().hex() == case.alias_hex
    assert str(parsed) == case.text


@given(case=get_strategy("account_id_valid_evm"))
def test_account_id_accepts_valid_evm_forms(case: AccountIdAliasCase) -> None:
    """Raw, prefixed, and scoped EVM-address inputs must parse without silent coercion."""
    parsed = AccountId.from_string(case.text)

    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.num == 0
    assert parsed.alias_key is None
    assert parsed.evm_address is not None
    assert parsed.evm_address.address_bytes.hex() == case.evm_hex
    assert str(parsed) == f"{case.shard}.{case.realm}.{case.evm_hex}"
    assert AccountId.from_string(str(parsed)) == parsed


@given(case=get_strategy("entity_id_valid_dotted"))
def test_token_id_accepts_valid_dotted_ids(case: EntityIdCase) -> None:
    """Valid dotted token IDs must parse and round-trip canonically."""
    _assert_token_roundtrip(case)


@given(case=get_strategy("entity_id_valid_checksum"))
def test_token_id_preserves_checksum_text(case: EntityIdCase) -> None:
    """Checksum-bearing token IDs must retain checksum metadata after parsing."""
    _assert_token_roundtrip(case)


@given(case=get_strategy("entity_id_valid_dotted"))
def test_contract_id_accepts_valid_dotted_ids(case: EntityIdCase) -> None:
    """Valid dotted contract IDs must parse and round-trip canonically."""
    _assert_contract_roundtrip(case)


@given(case=get_strategy("entity_id_valid_checksum"))
def test_contract_id_preserves_checksum_text(case: EntityIdCase) -> None:
    """Checksum-bearing contract IDs must retain checksum metadata after parsing."""
    _assert_contract_roundtrip(case)


@given(case=get_strategy("contract_id_valid_evm"))
def test_contract_id_accepts_scoped_evm_forms(case: AccountIdAliasCase) -> None:
    """Scoped 20-byte hex EVM addresses are a valid public ContractId format."""
    parsed = ContractId.from_string(case.text)

    assert parsed.shard == case.shard
    assert parsed.realm == case.realm
    assert parsed.contract == 0
    assert parsed.evm_address is not None
    assert parsed.evm_address.hex() == case.evm_hex
    assert str(parsed) == case.text
    assert ContractId.from_string(str(parsed)) == parsed


@given(value=get_strategy("entity_id_invalid_type"))
def test_account_id_rejects_non_string_inputs(value: object) -> None:
    """AccountId.from_string() documents a str-only API."""
    with pytest.raises(TypeError):
        AccountId.from_string(value)  # type: ignore[arg-type]


@given(value=get_strategy("entity_id_invalid_type"))
def test_token_id_rejects_non_string_inputs(value: object) -> None:
    """TokenId.from_string() must reject non-string inputs rather than coercing them."""
    if value is None:
        with pytest.raises(ValueError, match="cannot be None"):
            TokenId.from_string(value)  # type: ignore[arg-type]
    else:
        with pytest.raises(ValueError):
            TokenId.from_string(value)  # type: ignore[arg-type]


@given(value=get_strategy("entity_id_invalid_type"))
def test_contract_id_rejects_non_string_inputs(value: object) -> None:
    """ContractId.from_string() documents a str-only API."""
    with pytest.raises(TypeError):
        ContractId.from_string(value)  # type: ignore[arg-type]


@given(text=get_strategy("account_id_invalid_string"))
def test_account_id_rejects_invalid_strings(text: str) -> None:
    """Malformed account ID text must raise ValueError instead of partially parsing."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError):
            AccountId.from_string(text)


@given(text=get_strategy("token_id_invalid_string"))
def test_token_id_rejects_invalid_strings(text: str) -> None:
    """Malformed token ID text must raise ValueError."""
    with pytest.raises(ValueError, match="Invalid token ID string"):
        TokenId.from_string(text)


@given(text=get_strategy("contract_id_invalid_string"))
def test_contract_id_rejects_invalid_strings(text: str) -> None:
    """Malformed contract ID text must raise ValueError."""
    with pytest.raises(ValueError):
        ContractId.from_string(text)
