"""
Test the ContractLogInfo class.
"""

import pytest

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_log_info import ContractLogInfo
from hiero_sdk_python.hapi.services import basic_types_pb2, contract_types_pb2

pytestmark = pytest.mark.unit


def test_default_initialization():
    """Test ContractLogInfo initialization with default values."""
    log_info = ContractLogInfo()

    assert log_info.contract_id is None
    assert log_info.bloom is None
    assert log_info.topics == []
    assert log_info.data is None


def test_custom_initialization():
    """Test ContractLogInfo initialization with custom values."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    bloom = bytes.fromhex("1234")
    topics = [bytes.fromhex("abcd"), bytes.fromhex("ef01")]
    data = bytes.fromhex("5678")

    log_info = ContractLogInfo(
        contract_id=contract_id, bloom=bloom, topics=topics, data=data
    )

    assert log_info.contract_id == contract_id
    assert log_info.bloom == bloom
    assert log_info.topics == topics
    assert log_info.data == data


def test_str_representation():
    """Test string representation of ContractLogInfo."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    bloom = bytes.fromhex("1234")
    topics = [bytes.fromhex("abcd"), bytes.fromhex("ef01")]
    data = bytes.fromhex("5678")

    log_info = ContractLogInfo(
        contract_id=contract_id, bloom=bloom, topics=topics, data=data
    )

    string_repr = str(log_info)
    assert "ContractLogInfo" in string_repr
    assert "contract_id=1.2.3" in string_repr
    assert "bloom=1234" in string_repr
    assert "topics=['abcd', 'ef01']" in string_repr
    assert "data=5678" in string_repr


def test_to_proto():
    """Test converting ContractLogInfo to protobuf format."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    bloom = bytes.fromhex("1234")
    topics = [bytes.fromhex("abcd"), bytes.fromhex("ef01")]
    data = bytes.fromhex("5678")

    log_info = ContractLogInfo(
        contract_id=contract_id, bloom=bloom, topics=topics, data=data
    )

    proto = log_info._to_proto()

    assert isinstance(proto, contract_types_pb2.ContractLoginfo)
    assert proto.contractID == contract_id._to_proto()
    assert proto.bloom == bloom
    assert proto.topic == topics
    assert proto.data == data


def test_from_proto():
    """Test creating ContractLogInfo from protobuf format."""
    contract_id_proto = basic_types_pb2.ContractID(
        shardNum=1, realmNum=2, contractNum=3
    )

    proto = contract_types_pb2.ContractLoginfo(
        contractID=contract_id_proto,
        bloom=bytes.fromhex("1234"),
        topic=[bytes.fromhex("abcd"), bytes.fromhex("ef01")],
        data=bytes.fromhex("5678"),
    )

    log_info = ContractLogInfo._from_proto(proto)

    assert log_info.contract_id == ContractId(shard=1, realm=2, contract=3)
    assert log_info.bloom == bytes.fromhex("1234")
    assert log_info.topics == [bytes.fromhex("abcd"), bytes.fromhex("ef01")]
    assert log_info.data == bytes.fromhex("5678")


def test_from_proto_with_none():
    """Test creating ContractLogInfo from None proto raises ValueError."""
    with pytest.raises(ValueError, match="Contract log info proto is None"):
        ContractLogInfo._from_proto(None)


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    contract_id = ContractId(shard=5, realm=10, contract=15)
    bloom = bytes.fromhex("aabb")
    topics = [bytes.fromhex("ccdd"), bytes.fromhex("eeff")]
    data = bytes.fromhex("1122")

    original = ContractLogInfo(
        contract_id=contract_id, bloom=bloom, topics=topics, data=data
    )

    proto = original._to_proto()
    reconstructed = ContractLogInfo._from_proto(proto)

    assert reconstructed.contract_id == original.contract_id
    assert reconstructed.bloom == original.bloom
    assert reconstructed.topics == original.topics
    assert reconstructed.data == original.data
