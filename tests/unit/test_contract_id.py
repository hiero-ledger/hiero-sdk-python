import pytest
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit

def test_default_initialization():
    """Test ContractId initialization with default values."""
    contract_id = ContractId()
    
    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0

def test_custom_initialization():
    """Test ContractId initialization with custom values."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3

def test_str_representation():
    """Test string representation of ContractId."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    
    assert str(contract_id) == "1.2.3"

def test_str_representation_default():
    """Test string representation of ContractId with default values."""
    contract_id = ContractId()
    
    assert str(contract_id) == "0.0.0"

def test_from_string_valid():
    """Test creating ContractId from valid string format."""
    contract_id = ContractId.from_string("1.2.3")
    
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3

def test_from_string_with_spaces():
    """Test creating ContractId from string with leading/trailing spaces."""
    contract_id = ContractId.from_string("  1.2.3  ")
    
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3

def test_from_string_zeros():
    """Test creating ContractId from string with zero values."""
    contract_id = ContractId.from_string("0.0.0")
    
    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0

def test_from_string_large_numbers():
    """Test creating ContractId from string with large numbers."""
    contract_id = ContractId.from_string("999.888.777")
    
    assert contract_id.shard == 999
    assert contract_id.realm == 888
    assert contract_id.contract == 777

def test_from_string_invalid_format_too_few_parts():
    """Test creating ContractId from invalid string format with too few parts."""
    with pytest.raises(ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"):
        ContractId.from_string("1.2")

def test_from_string_invalid_format_too_many_parts():
    """Test creating ContractId from invalid string format with too many parts."""
    with pytest.raises(ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"):
        ContractId.from_string("1.2.3.4")

def test_from_string_invalid_format_non_numeric():
    """Test creating ContractId from invalid string format with non-numeric parts."""
    with pytest.raises(ValueError):
        ContractId.from_string("a.b.c")

def test_from_string_invalid_format_empty():
    """Test creating ContractId from empty string."""
    with pytest.raises(ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"):
        ContractId.from_string("")

def test_from_string_invalid_format_partial_numeric():
    """Test creating ContractId from string with some non-numeric parts."""
    with pytest.raises(ValueError):
        ContractId.from_string("1.a.3")

def test_to_proto():
    """Test converting ContractId to protobuf format."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    proto = contract_id._to_proto()
    
    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 3

def test_to_proto_default_values():
    """Test converting ContractId with default values to protobuf format."""
    contract_id = ContractId()
    proto = contract_id._to_proto()
    
    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.contractNum == 0

def test_from_proto():
    """Test creating ContractId from protobuf format."""
    proto = basic_types_pb2.ContractID(
        shardNum=1,
        realmNum=2,
        contractNum=3
    )
    
    contract_id = ContractId._from_proto(proto)
    
    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3

def test_from_proto_zero_values():
    """Test creating ContractId from protobuf format with zero values."""
    proto = basic_types_pb2.ContractID(
        shardNum=0,
        realmNum=0,
        contractNum=0
    )
    
    contract_id = ContractId._from_proto(proto)
    
    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0

def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = ContractId(shard=5, realm=10, contract=15)
    proto = original._to_proto()
    reconstructed = ContractId._from_proto(proto)
    
    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract

def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = ContractId(shard=7, realm=14, contract=21)
    string_repr = str(original)
    reconstructed = ContractId.from_string(string_repr)
    
    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract

def test_equality():
    """Test ContractId equality comparison."""
    contract_id1 = ContractId(shard=1, realm=2, contract=3)
    contract_id2 = ContractId(shard=1, realm=2, contract=3)
    contract_id3 = ContractId(shard=1, realm=2, contract=4)
    
    assert contract_id1 == contract_id2
    assert contract_id1 != contract_id3 