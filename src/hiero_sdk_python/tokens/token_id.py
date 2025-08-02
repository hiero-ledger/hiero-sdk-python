"""
hiero_sdk_python.tokens.token_id
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenId, a frozen dataclass for representing Hedera token identifiers
(shard, realm, num) with validation and protobuf conversion utilities.
"""
from dataclasses import dataclass
from typing import List, Optional
from hiero_sdk_python.hapi.services import basic_types_pb2

@dataclass(frozen=True, eq=True, init=True, repr=True)
class TokenId:
    """Immutable token identifier (shard, realm, num) with validation and protobuf conversion."""
    shard: int
    realm: int
    num: int

    def __post_init__(self) -> None:
        if not isinstance(self.shard, int):
            raise TypeError('Shard must be an integer')
        if not isinstance(self.realm, int):
            raise TypeError('Realm must be an integer')
        if not isinstance(self.num, int):
            raise TypeError('Num must be an integer')
        if self.shard < 0:
            raise ValueError('Shard must be >= 0')
        if self.realm < 0:
            raise ValueError('Realm must be >= 0')
        if self.num < 0:
            raise ValueError('Num must be >= 0')

    @classmethod
    def _from_proto(cls, token_id_proto: Optional[basic_types_pb2.TokenID] = None) -> "TokenId":
        """
        Creates a TokenId instance from a protobuf TokenID object.
        """
        if token_id_proto is None:
            raise ValueError('TokenId is required')
        if not isinstance(token_id_proto, basic_types_pb2.TokenID):
            raise TypeError('TokenId must be an instance of TokenID')

        return cls(
            shard=token_id_proto.shardNum,
            realm=token_id_proto.realmNum,
            num=token_id_proto.tokenNum
        )

    def _to_proto(self) -> basic_types_pb2.TokenID:
        """
        Converts the TokenId instance to a protobuf TokenID object.
        """
        token_id_proto = basic_types_pb2.TokenID()
        token_id_proto.shardNum = self.shard
        token_id_proto.realmNum = self.realm
        token_id_proto.tokenNum = self.num
        return token_id_proto

    @classmethod
    def from_string(cls, token_id_str: str = "") -> "TokenId":
        """
        Parses a string in the format 'shard.realm.num' to create a TokenId instance.
        """
        if token_id_str == "":
            raise ValueError('TokenId cannot be empty')
        if not isinstance(token_id_str, str):
            raise TypeError('TokenId must be a string')

        parts: List[str] = token_id_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError("Invalid TokenId format. Expected 'shard.realm.num'")
        return cls(shard=int(parts[0]), realm=int(parts[1]), num=int(parts[2]))

    def __str__(self) -> str:
        """
        Returns the string representation of the TokenId in the format 'shard.realm.num'.
        """
        return f"{self.shard}.{self.realm}.{self.num}"

    def __hash__(self) -> int:
        """ Returns a hash of the TokenId instance. """
        return hash((self.shard, self.realm, self.num))
