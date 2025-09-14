"""
hiero_sdk_python.tokens.token_id.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenId, a frozen dataclass for representing Hedera token identifiers
(shard, realm, num) with validation and protobuf conversion utilities.
"""
from dataclasses import dataclass
from typing import List, Optional

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string,
    format_to_string_with_checksum
)

@dataclass(frozen=True, eq=True, init=True, repr=True)
class TokenId:
    """Immutable token identifier (shard, realm, num) with validation and protobuf conversion."""
    shard: int
    realm: int
    num: int
    checksum: str|None = None

    def __post_init__(self) -> None:
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
    def from_string(cls, token_id_str: Optional[str] = None) -> "TokenId":
        """
        Parses a string in the format 'shard.realm.num' to create a TokenId instance.
        """
        if token_id_str == "":
            raise ValueError('TokenId cannot be empty')
        elif not isinstance(token_id_str, str):
            raise TypeError('TokenId must be a string')
        
        return parse_from_string(cls, token_id_str)
    
    def validate_checksum(self, client: Client):
        """Validate the checksum for the TokenId instance"""
        validate_checksum(
            shard=self.shard, 
            realm=self.realm,
            num=self.num, 
            checksum=self.checksum, 
            client=client
        )

    def to_string_with_checksum(self, client:Client):
        """
        Returns the string representation of the TokenId with checksum in the format 'shard.realm.num-checksum'
        """
        return format_to_string_with_checksum(
            shard=self.shard, 
            realm=self.realm, 
            num=self.num, 
            client=client
        )

    def __str__(self) -> str:
        """
        Returns the string representation of the TokenId in the format 'shard.realm.num'.
        """
        return format_to_string(self.shard, self.realm, self.realm)

    def __hash__(self) -> int:
        """ Returns a hash of the TokenId instance. """
        return hash((self.shard, self.realm, self.num))
