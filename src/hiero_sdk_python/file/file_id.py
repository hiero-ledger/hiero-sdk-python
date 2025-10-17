from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum
)


@dataclass
class FileId:
    """
    Represents a file ID on the network.

    A file ID consists of three components: shard, realm, and file (number).
    These components uniquely identify a file in the network.

    Attributes:
        shard (int): The shard number. Defaults to 0.
        realm (int): The realm number. Defaults to 0.
        file (int): The file number. Defaults to 0.
    """
    shard: int = 0
    realm: int = 0
    file: int = 0
    checksum: str | None = None
    
    @classmethod
    def _from_proto(cls, file_id_proto: basic_types_pb2.FileID) -> 'FileId':
        """
        Creates a FileId instance from a protobuf FileID object.
        """
        return cls(
            shard=file_id_proto.shardNum,
            realm=file_id_proto.realmNum,
            file=file_id_proto.fileNum
        )

    def _to_proto(self) -> basic_types_pb2.FileID:
        """
        Converts the FileId instance to a protobuf FileID object.
        """
        return basic_types_pb2.FileID(
            shardNum=self.shard,
            realmNum=self.realm,
            fileNum=self.file
        )
        
    @classmethod
    def from_string(cls, file_id_str: str) -> 'FileId':
        """
        Creates a FileId instance from a string in the format 'shard.realm.file'.
        """
        shard, realm, file, checksum = parse_from_string(file_id_str)
        file_id: FileId = cls(shard, realm, file)
        object.__setattr__(file_id, 'checksum', checksum)

        return file_id
    
    def __str__(self) -> str:
        """
        Returns a string representation of the FileId instance.
        """
        return f"{self.shard}.{self.realm}.{self.file}"
    
    def validate_checksum(self, client) -> None:
        """Validate the checksum for the FileId instance"""
        validate_checksum(
            shard=self.shard,
            realm=self.realm,
            num=self.num,
            checksum=self.checksum,
            client=client
        )

    def to_string_with_checksum(self, client) -> str:
        """
        Returns the string representation of the FileId with checksum 
        in the format 'shard.realm.num-checksum'
        """
        return format_to_string_with_checksum(
            shard=self.shard,
            realm=self.realm,
            num=self.num,
            client=client
        )