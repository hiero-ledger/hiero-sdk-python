"""
Unit tests for the DelegateContractId class.
"""

from __future__ import annotations

import struct
from unittest.mock import patch

import pytest

from hiero_sdk_python.contract.delegate_contract_id import DelegateContractId
from hiero_sdk_python.hapi.services import basic_types_pb2


pytestmark = pytest.mark.unit


@pytest.fixture
def client(mock_client):
    mock_client.network.ledger_id = bytes.fromhex("00")  # mainnet ledger id
    return mock_client


def test_default_initialization():
    """Test DelegateContractId initialization with default values."""
    contract_id = DelegateContractId()

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0
    assert contract_id.evm_address is None
    assert contract_id.checksum is None


def test_custom_initialization():
    """Test DelegateContractId initialization with custom values."""
    contract_id = DelegateContractId(shard=1, realm=2, contract=3)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address is None
    assert contract_id.checksum is None


def test_str_representation():
    """Test string representation of DelegateContractId."""
    contract_id = DelegateContractId(shard=1, realm=2, contract=3)

    assert isinstance(contract_id, DelegateContractId)
    assert str(contract_id) == "1.2.3"
    assert contract_id.evm_address is None
    assert contract_id.checksum is None


def test_str_representation_default():
    """Test string representation of DelegateContractId with default values."""
    contract_id = DelegateContractId()

    assert isinstance(contract_id, DelegateContractId)
    assert str(contract_id) == "0.0.0"
    assert contract_id.evm_address is None
    assert contract_id.checksum is None


@pytest.mark.parametrize(
    "contract_str, expected",
    [
        ("1.2.101", (1, 2, 101, None, None)),
        ("0.0.0", (0, 0, 0, None, None)),
        ("1.2.3-abcde", (1, 2, 3, None, "abcde")),
        (
            "1.2.abcdef0123456789abcdef0123456789abcdef01",
            (1, 2, 0, bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01"), None),
        ),
    ],
)
def test_from_string_for_valid_str(contract_str, expected):
    """Test creating DelegateContractId from valid string format."""
    shard, realm, contract, evm_address, checksum = expected

    contract_id = DelegateContractId.from_string(contract_str)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == shard
    assert contract_id.realm == realm
    assert contract_id.contract == contract
    assert contract_id.evm_address == evm_address
    assert contract_id.checksum == checksum


@pytest.mark.parametrize(
    "invalid_id",
    [
        "1.2",  # Too few parts
        "1.2.3.4",  # Too many parts
        "a.b.c",  # Non-numeric parts
        "",  # Empty string
        "1.a.3",  # Partial numeric
        "0.0.-1",
        "abc.def.ghi",
        "0.0.1-ad",
        "0.0.1-addefgh",
        "0.0.1 - abcde",
        " 0.0.100 ",
        " 1.2.abcdef0123456789abcdef0123456789abcdef01 ",
        "1.2.0xabcdef0123456789abcdef0123456789abcdef01",
        "1.2.001122334455667788990011223344556677",
        "1.2.000000000000000000000000000000000000000000",
    ],
)
def test_from_string_for_invalid_format(invalid_id):
    """Should raise error when creating DelegateContractId from invalid string input."""
    with pytest.raises(
        ValueError,
        match=f"Invalid contract ID string '{invalid_id}'. Expected format 'shard.realm.contract'.",
    ):
        DelegateContractId.from_string(invalid_id)


@pytest.mark.parametrize("invalid_id", [None, 123, True, object, {}])
def test_from_string_for_invalid_type(invalid_id):
    """Should raise error when creating DelegateContractId from invalid input type."""
    with pytest.raises(
        TypeError,
        match=f"contract_id_str must be of type str, got {type(invalid_id).__name__}",
    ):
        DelegateContractId.from_string(invalid_id)


def test_to_proto():
    """Test converting DelegateContractId to protobuf format."""
    contract_id = DelegateContractId(shard=1, realm=2, contract=3)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 3


def test_to_proto_default_values():
    """Test converting DelegateContractId with default values to protobuf format."""
    contract_id = DelegateContractId()
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.contractNum == 0


def test_from_proto():
    """Test creating DelegateContractId from protobuf format."""
    proto = basic_types_pb2.ContractID(shardNum=1, realmNum=2, contractNum=3)

    contract_id = DelegateContractId._from_proto(proto)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address is None


def test_from_proto_with_evm_address():
    """Test creating DelegateContractId from protobuf with EVM address set."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    proto = basic_types_pb2.ContractID(
        shardNum=1,
        realmNum=2,
        evm_address=evm_address,
    )

    contract_id = DelegateContractId._from_proto(proto)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 0
    assert contract_id.evm_address == evm_address


def test_from_proto_zero_values():
    """Test creating DelegateContractId from protobuf format with zero values."""
    proto = basic_types_pb2.ContractID(shardNum=0, realmNum=0, contractNum=0)

    contract_id = DelegateContractId._from_proto(proto)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0
    assert contract_id.evm_address is None


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = DelegateContractId(shard=5, realm=10, contract=15)
    proto = original._to_proto()
    reconstructed = DelegateContractId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract


def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = DelegateContractId(shard=7, realm=14, contract=21)
    string_repr = str(original)
    reconstructed = DelegateContractId.from_string(string_repr)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract


def test_equality():
    """Test DelegateContractId equality comparison."""
    contract_id1 = DelegateContractId(shard=1, realm=2, contract=3)
    contract_id2 = DelegateContractId(shard=1, realm=2, contract=3)
    contract_id3 = DelegateContractId(shard=1, realm=2, contract=4)

    assert contract_id1 == contract_id2
    assert contract_id1 != contract_id3


def test_evm_address_initialization():
    """Test DelegateContractId initialization with EVM address."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address)

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address == evm_address


def test_evm_address_to_proto():
    """Test converting DelegateContractId with EVM address to protobuf format."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 0
    assert proto.evm_address == evm_address


def test_evm_address_to_proto_none():
    """Test converting DelegateContractId with None EVM address to protobuf format."""
    contract_id = DelegateContractId(shard=1, realm=2, contract=3, evm_address=None)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 3
    assert proto.evm_address == b""


def test_evm_address_equality():
    """Test DelegateContractId equality with EVM addresses."""
    evm_address1 = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    evm_address2 = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")

    contract_id1 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id2 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id3 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address2)
    contract_id4 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=None)

    # Same EVM address should be equal
    assert contract_id1 == contract_id2

    # Different EVM addresses should not be equal
    assert contract_id1 != contract_id3

    # None EVM address should not be equal to one with EVM address
    assert contract_id1 != contract_id4


def test_evm_address_hash():
    """Test DelegateContractId hash with EVM addresses."""
    evm_address1 = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    evm_address2 = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")

    contract_id1 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id2 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id3 = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address2)

    # Same EVM address should have same hash
    assert hash(contract_id1) == hash(contract_id2)

    # Different EVM addresses should have different hashes
    assert hash(contract_id1) != hash(contract_id3)


def test_to_evm_address():
    """Test DelegateContractId.to_evm_address() for both explicit and computed EVM addresses."""
    # Explicit EVM address
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=1, realm=2, contract=3, evm_address=evm_address)
    assert contract_id.to_evm_address() == evm_address.hex()

    # Computed EVM address (no explicit evm_address)
    contract_id = DelegateContractId(shard=1, realm=2, contract=3)
    expected_bytes = struct.pack(">iqq", contract_id.shard, contract_id.realm, contract_id.contract)
    assert contract_id.to_evm_address() == expected_bytes.hex()

    # Default values
    contract_id = DelegateContractId()
    expected_bytes = struct.pack(">iqq", contract_id.shard, contract_id.realm, contract_id.contract)
    assert contract_id.to_evm_address() == expected_bytes.hex()


def test_str_representation_with_checksum(client):
    """Should return string representation with checksum"""
    contract_id = DelegateContractId.from_string("0.0.1")
    assert contract_id.to_string_with_checksum(client) == "0.0.1-dfkxr"


def test_str_representation_checksum_with_evm_address(client):
    """Should raise error on to_string_with_checksum is called when evm_address is set"""
    contract_id = DelegateContractId.from_string("0.0.abcdef0123456789abcdef0123456789abcdef01")

    with pytest.raises(
        ValueError,
        match="to_string_with_checksum cannot be applied to DelegateContractId with evm_address",
    ):
        contract_id.to_string_with_checksum(client)


def test_validate_checksum_success(client):
    """Should pass checksum validation when checksum is correct."""
    contract_id = DelegateContractId.from_string("0.0.1-dfkxr")
    contract_id.validate_checksum(client)


def test_validate_checksum_failure(client):
    """Should raise ValueError if checksum validation fails."""
    contract_id = DelegateContractId.from_string("0.0.1-wronx")

    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.1"):
        contract_id.validate_checksum(client)


def test_str_representation_with_evm_address():
    """Should return str representing with evm_address"""
    contract_id = DelegateContractId.from_string("0.0.abcdef0123456789abcdef0123456789abcdef01")
    assert contract_id.__str__() == "0.0.abcdef0123456789abcdef0123456789abcdef01"


def test_contract_id_repr_numeric():
    """Test __repr__ output for numeric contract ID."""
    contract_id = DelegateContractId(0, 0, 12345)
    expected = "DelegateContractId(shard=0, realm=0, contract=12345)"
    assert repr(contract_id) == expected


def test_contract_id_repr_evm_address():
    """Test __repr__ output for EVM-based contract ID."""
    evm_bytes = bytes.fromhex("a" * 40)
    contract_id = DelegateContractId(1, 2, evm_address=evm_bytes)
    expected = f"DelegateContractId(shard=1, realm=2, evm_address={evm_bytes.hex()})"
    assert repr(contract_id) == expected


def test_to_string_with_checksum_missing_ledger_id(mock_client):
    """Should raise error if client has no ledger ID."""
    mock_client.network.ledger_id = None
    contract_id = DelegateContractId.from_string("0.0.1")

    with pytest.raises(ValueError, match="Missing ledger ID"):
        contract_id.to_string_with_checksum(mock_client)


@pytest.mark.parametrize(
    "evm_address_str, expected",
    [
        (
            "abcdef0123456789abcdef0123456789abcdef01",
            (0, 0, 0, bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")),
        ),
        (
            "0xabcdef0123456789abcdef0123456789abcdef01",
            (0, 0, 0, bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")),
        ),
    ],
)
def test_from_evm_address_valid_params(evm_address_str, expected):
    """Test from_evm_address with valid EVM address strings."""
    shard, realm, contract, evm_address = expected

    contract_id = DelegateContractId.from_evm_address(0, 0, evm_address_str)

    assert isinstance(contract_id, DelegateContractId)
    assert contract_id.shard == shard
    assert contract_id.realm == realm
    assert contract_id.contract == contract
    assert contract_id.evm_address == evm_address
    assert contract_id.checksum is None


@pytest.mark.parametrize(
    "invalid_address",
    [
        "abcdef0123456789abcdef0123456789abcdef",  # less than 20 bytes
        "abcdef0123456789abcdef0123456789abcdef1010101",  # greater than 20 bytes
        "abcd-123sjd",  # invalid format
        "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",  # invalid hex
    ],
)
def test_from_evm_address_invalid_evm_address_str(invalid_address):
    """Test from_evm_address raise error for invalid EVM address strings."""
    with pytest.raises(ValueError, match=f"Invalid EVM address: {invalid_address}"):
        DelegateContractId.from_evm_address(0, 0, invalid_address)


@pytest.mark.parametrize(
    "invalid_address",
    [None, 1234, True, object, {}],
)
def test_from_evm_address_invalid_evm_address_type(invalid_address):
    """Test from_evm_address raise error for non-string EVM address inputs."""
    with pytest.raises(
        TypeError,
        match=f"evm_address must be of type str, got {type(invalid_address).__name__}",
    ):
        DelegateContractId.from_evm_address(0, 0, invalid_address)


@pytest.mark.parametrize(
    "invalid_shard",
    [None, "123", True, object, {}],
)
def test_from_evm_address_invalid_shard_type(invalid_shard):
    """Test from_evm_address raise error for invalid shard types."""
    with pytest.raises(TypeError, match=f"shard must be int, got {type(invalid_shard).__name__}"):
        DelegateContractId.from_evm_address(invalid_shard, 0, "abcdef0123456789abcdef0123456789abcdef01")


def test_from_evm_address_negative_shard_value():
    """Test from_evm_address raise error for negative shard values."""
    with pytest.raises(ValueError, match="shard must be a non-negative integer"):
        DelegateContractId.from_evm_address(-1, 0, "abcdef0123456789abcdef0123456789abcdef01")


@pytest.mark.parametrize(
    "invalid_realm",
    [None, "123", True, object, {}],
)
def test_from_evm_address_invalid_realm_type(invalid_realm):
    """Test from_evm_address raise error for invalid realm types."""
    with pytest.raises(TypeError, match=f"realm must be int, got {type(invalid_realm).__name__}"):
        DelegateContractId.from_evm_address(0, invalid_realm, "abcdef0123456789abcdef0123456789abcdef01")


def test_from_evm_address_negative_realm_value():
    """Test from_evm_address raise error for negative realm values."""
    with pytest.raises(ValueError, match="realm must be a non-negative integer"):
        DelegateContractId.from_evm_address(0, -1, "abcdef0123456789abcdef0123456789abcdef01")


def test_from_bytes_success():
    """Should deserialize DelegateContractId correctly from protobuf bytes."""
    original = DelegateContractId(shard=1, realm=2, contract=3)
    data = original.to_bytes()

    reconstructed = DelegateContractId.from_bytes(data)

    assert reconstructed == original


@pytest.mark.parametrize("invalid_data", [None, "abc", 123, object()])
def test_from_bytes_invalid_type(invalid_data):
    """Should raise TypeError when from_bytes receives non-bytes input."""
    with pytest.raises(TypeError, match="data must be bytes"):
        DelegateContractId.from_bytes(invalid_data)


def test_from_bytes_invalid_payload():
    """Should raise ValueError when protobuf deserialization fails."""
    with pytest.raises(ValueError, match="Failed to deserialize ContractId from bytes"):
        DelegateContractId.from_bytes(b"\x00\x01\x02")


def test_populate_contract_num_success(client):
    """Should populate contract number using mirror node response."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=0, realm=0, evm_address=evm_address)

    with patch(
        "hiero_sdk_python.contract.contract_id.perform_query_to_mirror_node",
        return_value={"contract_id": "0.0.123"},
    ):
        populated = contract_id.populate_contract_num(client)

    assert populated.contract == 123
    assert populated.evm_address == evm_address


def test_populate_contract_num_invalid_response(client):
    """Should raise error when populating contract number invalid response."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=0, realm=0, evm_address=evm_address)

    with (
        patch(
            "hiero_sdk_python.contract.contract_id.perform_query_to_mirror_node",
            return_value={"contract_id": "invalid.account.format"},
        ),
        pytest.raises(
            ValueError,
            match="Invalid contract_id format received: invalid.account.format",
        ),
    ):
        contract_id.populate_contract_num(client)


def test_populate_contract_num_query_fails(client):
    """Should raise error when populating contract number query fails."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=0, realm=0, evm_address=evm_address)

    with (
        patch(
            "hiero_sdk_python.contract.contract_id.perform_query_to_mirror_node",
            side_effect=RuntimeError("mirror node query error"),
        ),
        pytest.raises(
            RuntimeError,
            match="Failed to populate contract num from mirror node for evm_address abcdef0123456789abcdef0123456789abcdef01",
        ),
    ):
        contract_id.populate_contract_num(client)


def test_populate_contract_num_without_evm_address(client):
    """Should raise error when populate_contract_num is called without evm_address."""
    contract_id = DelegateContractId(shard=0, realm=0, contract=1)

    with pytest.raises(ValueError, match="evm_address is required to populate the contract number"):
        contract_id.populate_contract_num(client)


def test_populate_contract_num_invalid_mirror_response(client):
    """Should raise error if mirror node response is missing contract_id."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = DelegateContractId(shard=0, realm=0, evm_address=evm_address)

    with (
        patch(
            "hiero_sdk_python.contract.contract_id.perform_query_to_mirror_node",
            return_value={},
        ),
        pytest.raises(ValueError, match="Mirror node response missing 'contract_id'"),
    ):
        contract_id.populate_contract_num(client)


def test_to_proto_key():
    """Test to_proto_key returns the Key protobuf."""
    contract_id = DelegateContractId(shard=0, realm=0, contract=1)
    key = contract_id.to_proto_key()

    assert key is not None
    assert key.delegatable_contract_id is not None
    assert key.delegatable_contract_id.shardNum == contract_id.shard
    assert key.delegatable_contract_id.realmNum == contract_id.realm
    assert key.delegatable_contract_id.contractNum == contract_id.contract
