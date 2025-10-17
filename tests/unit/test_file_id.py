import pytest
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit

def test_default_initialization():
    """Test FileId initialization with default values."""
    file_id = FileId()
    
    assert file_id.shard == 0
    assert file_id.realm == 0
    assert file_id.file == 0
    assert file_id.checksum == None

def test_custom_initialization():
    """Test FileId initialization with custom values."""
    file_id = FileId(shard=1, realm=2, file=3)
    
    assert file_id.shard == 1
    assert file_id.realm == 2
    assert file_id.file == 3
    assert file_id.checksum == None

def test_str_representation():
    """Test string representation of FileId."""
    file_id = FileId(shard=1, realm=2, file=3)
    
    assert str(file_id) == "1.2.3"

def test_str_representation_default():
    """Test string representation of FileId with default values."""
    file_id = FileId()
    
    assert str(file_id) == "0.0.0"

def test_from_string_valid():
    """Test creating FileId from valid string format."""
    file_id = FileId.from_string("1.2.3")
    
    assert file_id.shard == 1
    assert file_id.realm == 2
    assert file_id.file == 3

def test_from_string_with_spaces():
    """Test creating FileId from string with leading/trailing spaces."""
    file_id = FileId.from_string("1.2.3")
    
    assert file_id.shard == 1
    assert file_id.realm == 2
    assert file_id.file == 3

def test_from_string_zeros():
    """Test creating FileId from string with zero values."""
    file_id = FileId.from_string("0.0.0")
    
    assert file_id.shard == 0
    assert file_id.realm == 0
    assert file_id.file == 0

def test_from_string_large_numbers():
    """Test creating FileId from string with large numbers."""
    file_id = FileId.from_string("999.888.777")
    
    assert file_id.shard == 999
    assert file_id.realm == 888
    assert file_id.file == 777

def test_from_string_invalid_format_too_few_parts():
    """Test creating FileId from invalid string format with too few parts."""
    with pytest.raises(ValueError, match="Invalid format for entity ID"):
        FileId.from_string("1.2")

def test_from_string_invalid_format_too_many_parts():
    """Test creating FileId from invalid string format with too many parts."""
    with pytest.raises(ValueError, match="Invalid format for entity ID"):
        FileId.from_string("1.2.3.4")

def test_from_string_invalid_format_non_numeric():
    """Test creating FileId from invalid string format with non-numeric parts."""
    with pytest.raises(ValueError):
        FileId.from_string("a.b.c")

def test_from_string_invalid_format_empty():
    """Test creating FileId from empty string."""
    with pytest.raises(ValueError, match="Invalid format for entity ID"):
        FileId.from_string("")

def test_from_string_invalid_format_partial_numeric():
    """Test creating FileId from string with some non-numeric parts."""
    with pytest.raises(ValueError):
        FileId.from_string("1.a.3")

def test_to_proto():
    """Test converting FileId to protobuf format."""
    file_id = FileId(shard=1, realm=2, file=3)
    proto = file_id._to_proto()
    
    assert isinstance(proto, basic_types_pb2.FileID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.fileNum == 3

def test_to_proto_default_values():
    """Test converting FileId with default values to protobuf format."""
    file_id = FileId()
    proto = file_id._to_proto()
    
    assert isinstance(proto, basic_types_pb2.FileID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.fileNum == 0

def test_from_proto():
    """Test creating FileId from protobuf format."""
    proto = basic_types_pb2.FileID(
        shardNum=1,
        realmNum=2,
        fileNum=3
    )
    
    file_id = FileId._from_proto(proto)
    
    assert file_id.shard == 1
    assert file_id.realm == 2
    assert file_id.file == 3

def test_from_proto_zero_values():
    """Test creating FileId from protobuf format with zero values."""
    proto = basic_types_pb2.FileID(
        shardNum=0,
        realmNum=0,
        fileNum=0
    )
    
    file_id = FileId._from_proto(proto)
    
    assert file_id.shard == 0
    assert file_id.realm == 0
    assert file_id.file == 0

def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = FileId(shard=5, realm=10, file=15)
    proto = original._to_proto()
    reconstructed = FileId._from_proto(proto)
    
    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.file == reconstructed.file

def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = FileId(shard=7, realm=14, file=21)
    string_repr = str(original)
    reconstructed = FileId.from_string(string_repr)
    
    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.file == reconstructed.file

def test_equality():
    """Test FileId equality comparison."""
    file_id1 = FileId(shard=1, realm=2, file=3)
    file_id2 = FileId(shard=1, realm=2, file=3)
    file_id3 = FileId(shard=1, realm=2, file=4)
    
    assert file_id1 == file_id2
    assert file_id1 != file_id3 