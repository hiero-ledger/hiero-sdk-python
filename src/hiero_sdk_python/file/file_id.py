from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2


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
        parts = file_id_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError("Invalid file ID string format. Expected 'shard.realm.file'")
        shard, realm, file = map(int, parts)
        return cls(shard, realm, file)
    
    def __str__(self) -> str:
        """
        Returns a string representation of the FileId instance.
        """
        return f"{self.shard}.{self.realm}.{self.file}"