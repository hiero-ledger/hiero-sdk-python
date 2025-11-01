"""
hiero_sdk_python.tokens.token_id.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenId, a frozen dataclass for representing Hedera token identifiers
(shard, realm, num) with validation and protobuf conversion utilities.
"""
from dataclasses import dataclass, field
from typing import Optional

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
    """Represents an immutable Hedera token identifier (shard, realm, num).

    This is a frozen dataclass providing validation, string parsing,
    and protobuf conversion utilities for a token ID.

    Attributes:
        shard (int): The shard number (non-negative).
        realm (int): The realm number (non-negative).
        num (int): The entity number (non-negative).
        checksum (str | None): An optional checksum, automatically populated
            when parsing from a string with a checksum. Not directly
            initializable.
    """
    shard: int
    realm: int
    num: int
    checksum: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """
        Validates that shard, realm, and num are non-negative after initialization.

        Raises:
            ValueError: If shard, realm, or num is less than 0.
        """
        if self.shard < 0:
            raise ValueError('Shard must be >= 0')
        if self.realm < 0:
            raise ValueError('Realm must be >= 0')
        if self.num < 0:
            raise ValueError('Num must be >= 0')

    @classmethod
    def _from_proto(cls, token_id_proto: Optional[basic_types_pb2.TokenID] = None) -> "TokenId":
        """Creates a TokenId instance from a protobuf TokenID object.

        Args:
            token_id_proto (Optional[basic_types_pb2.TokenID]): The protobuf
                TokenID object.

        Returns:
            TokenId: The corresponding TokenId instance.

        Raises:
            ValueError: If token_id_proto is None.
        """
        if token_id_proto is None:
            raise ValueError('TokenId is required')

        return cls(
            shard=token_id_proto.shardNum,
            realm=token_id_proto.realmNum,
            num=token_id_proto.tokenNum
        )

    def _to_proto(self) -> basic_types_pb2.TokenID:
        """Converts the TokenId instance to a protobuf TokenID object.

        Returns:
            basic_types_pb2.TokenID: The corresponding protobuf TokenID object.
        """
        token_id_proto = basic_types_pb2.TokenID()
        token_id_proto.shardNum = self.shard
        token_id_proto.realmNum = self.realm
        token_id_proto.tokenNum = self.num
        return token_id_proto

    @classmethod
    def from_string(cls, token_id_str: Optional[str] = None) -> "TokenId":
        """Parses a string to create a TokenId instance.

        The string can be in the format 'shard.realm.num' or
        'shard.realm.num-checksum'.

        Args:
            token_id_str (Optional[str]): The token ID string to parse.

        Returns:
            TokenId: The corresponding TokenId instance.

        Raises:
            ValueError: If the token_id_str is None, empty, or in an
                invalid format.
        """
        if token_id_str is None:
            raise ValueError("token_id_str cannot be None") 

        try:
            shard, realm, num, checksum = parse_from_string(token_id_str)

            token_id = cls(
                shard=int(shard),
                realm=int(realm),
                num=int(num))
            object.__setattr__(token_id, 'checksum', checksum)

            return token_id
        except Exception as e:
            raise ValueError(
                f"Invalid token ID string '{token_id_str}'. Expected format 'shard.realm.num'."
            )from e

    def validate_checksum(self, client: Client) -> None:
        """Validates the checksum (if present) against the client's network.

        Args:
            client (Client): The client instance, used to determine the
                network ledger ID for validation.

        Raises:
            ValueError: If the client's ledger ID is not set (required for
                validation).
            ValueError: If the checksum is present but does not match the
                expected checksum for the client's network (e.g.,
                "Checksum mismatch for 0.0.123").
        """
        validate_checksum(
            shard=self.shard,
            realm=self.realm,
            num=self.num,
            checksum=self.checksum,
            client=client
        )

    def to_string_with_checksum(self, client:Client) -> str:
        """Returns the string representation with a network-specific checksum.

        Generates a checksum based on the client's network and returns
        the ID in 'shard.realm.num-checksum' format.

        Args:
            client (Client): The client instance used to generate the
                network-specific checksum.

        Returns:
            str: The token ID string with a calculated checksum.
        """
        return format_to_string_with_checksum(
            shard=self.shard,
            realm=self.realm,
            num=self.num,
            client=client
        )

    def __str__(self) -> str:
        """Returns the simple string representation 'shard.realm.num'.

        Returns:
            str: The token ID string in 'shard.realm.num' format.
        """
        return format_to_string(self.shard, self.realm, self.num)

    def __hash__(self) -> int:
        """Generates a hash based on the shard, realm, and num.

        Returns:
            int: A hash of the TokenId instance.
        """
        return hash((self.shard, self.realm, self.num))
