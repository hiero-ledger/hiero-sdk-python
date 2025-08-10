"""
Test the ContractNonceInfo class.
"""

import pytest

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_nonce_info import ContractNonceInfo
from hiero_sdk_python.hapi.services import contract_types_pb2

pytestmark = pytest.mark.unit


def test_default_initialization():
    """Test ContractNonceInfo initialization with default values."""
    nonce_info = ContractNonceInfo()

    assert nonce_info.contract_id is None
    assert nonce_info.nonce == 0


def test_custom_initialization():
    """Test ContractNonceInfo initialization with custom values."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    nonce = 42

    nonce_info = ContractNonceInfo(contract_id=contract_id, nonce=nonce)

    assert nonce_info.contract_id == contract_id
    assert nonce_info.nonce == nonce


def test_str_representation():
    """Test string representation of ContractNonceInfo."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    nonce = 42

    nonce_info = ContractNonceInfo(contract_id=contract_id, nonce=nonce)

    string_repr = str(nonce_info)

    # Even without a custom __str__ method, the dataclass should provide a readable representation
    assert "ContractNonceInfo" in string_repr
    assert "contract_id" in string_repr
    assert "1.2.3" in string_repr or "ContractId" in string_repr
    assert "nonce=42" in string_repr


def test_to_proto():
    """Test converting ContractNonceInfo to protobuf format."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    nonce = 42

    nonce_info = ContractNonceInfo(contract_id=contract_id, nonce=nonce)

    proto = nonce_info._to_proto()

    assert isinstance(proto, contract_types_pb2.ContractNonceInfo)
    assert proto.contract_id == contract_id._to_proto()
    assert proto.nonce == nonce


def test_from_proto():
    """Test creating ContractNonceInfo from protobuf format."""
    contract_id_proto = ContractId(shard=1, realm=2, contract=3)._to_proto()

    proto = contract_types_pb2.ContractNonceInfo(
        contract_id=contract_id_proto,
        nonce=42,
    )

    nonce_info = ContractNonceInfo._from_proto(proto)

    assert nonce_info.contract_id == ContractId(shard=1, realm=2, contract=3)
    assert nonce_info.nonce == 42


def test_from_proto_with_none():
    """Test creating ContractNonceInfo from None proto raises ValueError."""
    with pytest.raises(ValueError, match="Contract nonce info proto is None"):
        ContractNonceInfo._from_proto(None)


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    contract_id = ContractId(shard=5, realm=10, contract=15)
    nonce = 123

    original = ContractNonceInfo(contract_id=contract_id, nonce=nonce)

    proto = original._to_proto()
    reconstructed = ContractNonceInfo._from_proto(proto)

    assert reconstructed.contract_id == original.contract_id
    assert reconstructed.nonce == original.nonce
