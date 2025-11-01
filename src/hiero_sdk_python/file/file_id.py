"""
FileId class.

This module defines the FileId object, which serves as a unique identifier for
files stored on the Hedera network. It supports string parsing, checksum validation,
and conversion to and from protobuf structures.
"""
from dataclasses import dataclass, field
from typing import Optional 

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum
)


@dataclass(frozen=True)
class FileId:
    """
    Represents a file ID on the network.

    A file ID consists of three components: shard, realm, and file number.
    These components uniquely identify a file in the network.

    Attributes:
        shard (int): The shard number. Defaults to 0.
        realm (int): The realm number. Defaults to 0.
        file (int): The file number. Defaults to 0.
        checksum (Optional[str]): The calculated checksum for the file ID.
    """
    shard: int = 0
    realm: int = 0
    file: int = 0
    checksum: Optional[str] = field(default=None, init=False)

    @classmethod
    def _from_proto(cls, file_id_proto: basic_types_pb2.FileID) -> 'FileId':
        """
        Creates a FileId instance from a protobuf FileID object.

        Args:
            file_id_proto (basic_types_pb2.FileID): The protobuf object containing
                the file ID components.

        Returns:
            FileId: A new instance of the FileId class.
        """
        return cls(
            shard=file_id_proto.shardNum,
            realm=file_id_proto.realmNum,
            file=file_id_proto.fileNum
        )

    def _to_proto(self) -> basic_types_pb2.FileID:
        """
        Converts the FileId instance to a protobuf FileID object.

        Returns:
            basic_types_pb2.FileID: The protobuf representation of the FileId.
        """
        return basic_types_pb2.FileID(
            shardNum=self.shard,
            realmNum=self.realm,
            fileNum=self.file
        )

    @classmethod
    def from_string(cls, file_id_str: str) -> 'FileId':
        """
        Parses a string in the format 'shard.realm.file' (with optional checksum) 
        to create a FileId instance.

        Args:
            file_id_str (str): The string representation of the File ID.

        Returns:
            FileId: A new instance with components and checksum (if present).

        Raises:
            ValueError: If the input string is malformed or cannot be parsed.
        """
        try:
            shard, realm, file, checksum = parse_from_string(file_id_str)

            file_id: FileId = cls(
                shard=int(shard),
                realm=int(realm),
                file=int(file)
            )
            object.__setattr__(file_id, 'checksum', checksum)

            return file_id
        except Exception as e: 
            raise ValueError(
                f"Invalid file ID string '{file_id_str}'. Expected format 'shard.realm.file'."
            ) from e
    def __str__(self) -> str:
        """
        Returns the string representation of the FileId in the format 'shard.realm.file'.

        Returns:
            str: The string representation of the file ID components.
        """
        return f"{self.shard}.{self.realm}.{self.file}"

    def validate_checksum(self, client: Client) -> None:
        """
        Validates the stored checksum against the calculated checksum using the provided client.

        Args:
            client (Client): The client instance used to retrieve network information 
                necessary for checksum calculation.

        Raises:
            ValueError: If the stored checksum is invalid or does not match the calculated value.
        """
        validate_checksum(
            self.shard,
            self.realm,
            self.file,
            self.checksum,
            client
        )

    def to_string_with_checksum(self, client: Client) -> str:
        """
        Returns the string representation of the FileId with its calculated checksum 
        in 'shard.realm.file-checksum' format.

        Args:
            client (Client): The client instance used to retrieve network information 
                necessary for checksum calculation.

        Returns:
            str: The file ID formatted with its checksum.
        """
        return format_to_string_with_checksum(
            self.shard,
            self.realm,
            self.file,
            client
        )