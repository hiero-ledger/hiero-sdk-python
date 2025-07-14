from dataclasses import dataclass, field
import datetime
from typing import Optional
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.hapi.services.file_get_info_pb2 import FileGetInfoResponse
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto

@dataclass
class FileInfo:
    """
    Information about a file stored on the Hedera network.
    
    Attributes:
        file_id (Optional[FileId]): The ID of the file
        size (Optional[int]): The size of the file in bytes
        expiration_time (Optional[Timestamp]): When the file will expire
        is_deleted (Optional[bool]): Whether the file has been deleted
        keys (list[PublicKey]): The keys that can modify this file
        file_memo (Optional[str]): The memo associated with the file
        ledger_id (Optional[bytes]): The ID of the ledger this file exists in
    """
    file_id: Optional[FileId] = None
    size: Optional[int] = None
    expiration_time: Optional[Timestamp] = None
    is_deleted: Optional[bool] = None
    keys: list[PublicKey] = field(default_factory=list)
    file_memo: Optional[str] = None
    ledger_id: Optional[bytes] = None

    @classmethod
    def _from_proto(cls, proto: FileGetInfoResponse.FileInfo) -> 'FileInfo':
        """
        Creates a FileInfo instance from its protobuf representation.

        Args:
            proto (FileGetInfoResponse.FileInfo): The protobuf to convert from.

        Returns:
            FileInfo: A new FileInfo instance.
        """
        if proto is None:
            raise ValueError("File info proto is None")
        
        return cls(
            file_id=FileId._from_proto(proto.fileID),
            size=proto.size,
            expiration_time=Timestamp._from_protobuf(proto.expirationTime),
            is_deleted=proto.deleted,
            keys=[PublicKey._from_proto(key) for key in proto.keys.keys],
            file_memo=proto.memo,
            ledger_id=proto.ledger_id
        )

    def _to_proto(self) -> FileGetInfoResponse.FileInfo:
        """
        Converts this FileInfo instance to its protobuf representation.

        Returns:
            FileGetInfoResponse.FileInfo: The protobuf representation of this FileInfo.
        """
        return FileGetInfoResponse.FileInfo(
            fileID=self.file_id._to_proto() if self.file_id else None,
            size=self.size,
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            deleted=self.is_deleted,
            keys=KeyListProto(keys=[key._to_proto() for key in self.keys or []]),
            memo=self.file_memo,
            ledger_id=self.ledger_id
        )
        
    def __repr__(self) -> str:
        """
        Returns a string representation of the FileInfo object.

        Returns:
            str: A string representation of the FileInfo object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the FileInfo.
        """
        # Format expiration time as datetime if available
        exp_dt = (
            datetime.datetime.fromtimestamp(self.expiration_time.seconds)
            if self.expiration_time and hasattr(self.expiration_time, "seconds")
            else self.expiration_time
        )

        # Format keys as readable strings
        keys_str = [key.to_string() for key in self.keys] if self.keys else []

        # Format ledger_id as hex if it's bytes
        ledger_id_display = (
            f"0x{self.ledger_id.hex()}"
            if isinstance(self.ledger_id, (bytes, bytearray))
            else self.ledger_id
        )

        return (
            "FileInfo(\n"
            f"  file_id={self.file_id},\n"
            f"  size={self.size},\n"
            f"  expiration_time={exp_dt},\n"
            f"  is_deleted={self.is_deleted},\n"
            f"  keys={keys_str},\n"
            f"  file_memo='{self.file_memo}',\n"
            f"  ledger_id={ledger_id_display}\n"
            ")"
        )