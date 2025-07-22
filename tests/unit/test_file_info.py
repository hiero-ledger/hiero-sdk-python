"""
Unit tests for the FileInfo class.
"""

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info import FileInfo
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.file_get_info_pb2 import FileGetInfoResponse
from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


@pytest.fixture
def file_info():
    """Fixture for a FileInfo object"""
    return FileInfo(
        file_id=FileId(0, 0, 100),
        size=1024,
        expiration_time=Timestamp(1625097600, 0),
        is_deleted=False,
        keys=[PrivateKey.generate_ed25519().public_key()],
        file_memo="Test file memo",
        ledger_id=b"test_ledger_id",
    )


@pytest.fixture
def proto_file_info():
    """Fixture for a proto FileInfo object"""
    public_key = PrivateKey.generate_ed25519().public_key()
    proto = FileGetInfoResponse.FileInfo(
        fileID=FileId(0, 0, 100)._to_proto(),
        size=1024,
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        deleted=False,
        keys=KeyListProto(keys=[public_key._to_proto()]),
        memo="Test file memo",
        ledger_id=b"test_ledger_id",
    )
    return proto


def test_file_info_initialization(file_info):
    """Test the initialization of the FileInfo class"""
    assert file_info.file_id == FileId(0, 0, 100)
    assert file_info.size == 1024
    assert file_info.expiration_time == Timestamp(1625097600, 0)
    assert file_info.is_deleted is False
    assert len(file_info.keys) == 1
    assert file_info.keys[0] is not None
    assert file_info.file_memo == "Test file memo"
    assert file_info.ledger_id == b"test_ledger_id"


def test_file_info_default_initialization():
    """Test the default initialization of the FileInfo class"""
    file_info = FileInfo()
    assert file_info.file_id is None
    assert file_info.size is None
    assert file_info.expiration_time is None
    assert file_info.is_deleted is None
    assert file_info.keys == []
    assert file_info.file_memo is None
    assert file_info.ledger_id is None


def test_from_proto(proto_file_info):
    """Test the from_proto method of the FileInfo class"""
    file_info = FileInfo._from_proto(proto_file_info)

    assert file_info.file_id == FileId(0, 0, 100)
    assert file_info.size == 1024
    assert file_info.expiration_time == Timestamp(1625097600, 0)
    assert file_info.is_deleted is False
    assert len(file_info.keys) == 1
    assert file_info.keys[0] is not None
    assert file_info.file_memo == "Test file memo"
    assert file_info.ledger_id == b"test_ledger_id"


def test_from_proto_with_empty_keys():
    """Test the from_proto method of the FileInfo class with empty keys"""
    proto = FileGetInfoResponse.FileInfo(
        fileID=FileId(0, 0, 100)._to_proto(),
        size=1024,
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        deleted=False,
        keys=KeyListProto(keys=[]),
        memo="Test file memo",
        ledger_id=b"test_ledger_id",
    )

    file_info = FileInfo._from_proto(proto)
    assert file_info.file_id == FileId(0, 0, 100)
    assert file_info.size == 1024
    assert file_info.keys == []


def test_from_proto_none_raises_error():
    """Test the from_proto method of the FileInfo class with a None proto"""
    with pytest.raises(ValueError, match="File info proto is None"):
        FileInfo._from_proto(None)


def test_to_proto(file_info):
    """Test the to_proto method of the FileInfo class"""
    proto = file_info._to_proto()

    assert proto.fileID == FileId(0, 0, 100)._to_proto()
    assert proto.size == 1024
    assert proto.expirationTime == Timestamp(1625097600, 0)._to_protobuf()
    assert proto.deleted is False
    assert len(proto.keys.keys) == 1
    assert proto.keys.keys[0] is not None
    assert proto.memo == "Test file memo"
    assert proto.ledger_id == b"test_ledger_id"


def test_to_proto_with_none_values():
    """Test the to_proto method of the FileInfo class with none values"""
    file_info = FileInfo()
    proto = file_info._to_proto()

    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, "fileID")
    assert proto.size == 0  # 0 is default for protobuf int when None is passed
    assert hasattr(proto, "expirationTime")
    assert proto.deleted is False  # False is default for protobuf bool
    assert proto.keys.keys == []  # Empty list for keys
    assert proto.memo == ""  # Empty string is default for protobuf
    assert proto.ledger_id == b""  # Empty bytes is default for protobuf


def test_to_proto_with_empty_keys():
    """Test the to_proto method of the FileInfo class with empty keys list"""
    file_info = FileInfo(file_id=FileId(0, 0, 100), size=1024, keys=[])
    proto = file_info._to_proto()

    assert proto.fileID == FileId(0, 0, 100)._to_proto()
    assert proto.size == 1024
    assert proto.keys.keys == []


def test_proto_conversion(file_info):
    """Test converting FileInfo to proto and back preserves data"""
    proto = file_info._to_proto()
    converted_file_info = FileInfo._from_proto(proto)

    assert converted_file_info.file_id == file_info.file_id
    assert converted_file_info.size == file_info.size
    assert converted_file_info.expiration_time == file_info.expiration_time
    assert converted_file_info.is_deleted == file_info.is_deleted
    assert len(converted_file_info.keys) == len(file_info.keys)
    assert converted_file_info.file_memo == file_info.file_memo
    assert converted_file_info.ledger_id == file_info.ledger_id


def test_proto_conversion_with_multiple_keys():
    """Test converting FileInfo with multiple keys to proto and back preserves data"""
    file_info = FileInfo(
        file_id=FileId(0, 0, 100),
        size=2048,
        keys=[
            PrivateKey.generate_ed25519().public_key(),
            PrivateKey.generate_ed25519().public_key(),
        ],
    )

    proto = file_info._to_proto()
    converted_file_info = FileInfo._from_proto(proto)

    assert converted_file_info.file_id == file_info.file_id
    assert converted_file_info.size == file_info.size
    assert len(converted_file_info.keys) == len(file_info.keys)
    assert len(converted_file_info.keys) == 2
