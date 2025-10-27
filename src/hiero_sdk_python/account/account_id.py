"""
AccountId class.
"""

import re
from typing import TYPE_CHECKING

from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum
)

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

ALIAS_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.((?:[0-9a-fA-F][0-9a-fA-F])+)$")

class AccountId:
    """
    Represents an account ID on the network.

    An account ID consists of three components: shard, realm, and num.
    These components uniquely identify an account in the network.

    The standard format is `<shardNum>.<realmNum>.<accountNum>`, e.g., `0.0.10`.

    In addition to the account number, the account component can also be an alias:
    - An alias can be either a public key (ED25519 or ECDSA)
    - The alias format is `<shardNum>.<realmNum>.<alias>`, where `alias` is the public key
    """

    def __init__(
        self, shard: int = 0, realm: int = 0, num: int = 0, alias_key: PublicKey = None
    ) -> None:
        """
        Initialize a new AccountId instance.
        Args:
            shard (int): The shard number of the account.
            realm (int): The realm number of the account.
            num (int): The account number.
            alias_key (PublicKey): The public key of the account.
        """
        self.shard = shard
        self.realm = realm
        self.num = num
        self.alias_key = alias_key
        self.__checksum: str | None = None

    @classmethod
    def from_string(cls, account_id_str: str) -> "AccountId":
        """
        Creates an AccountId instance from a string in the format 'shard.realm.num'.
        """
        if account_id_str is None or not isinstance(account_id_str, str):
            raise ValueError(f"Invalid account ID string '{account_id_str}'. Expected format 'shard.realm.num'.")

        try:
            shard, realm, num, checksum = parse_from_string(account_id_str)

            account_id: AccountId = cls(
                shard=int(shard),
                realm=int(realm),
                num=int(num)
            )
            account_id.__checksum = checksum

            return account_id
        except Exception as e:
            alias_match = ALIAS_REGEX.match(account_id_str)
            
            if alias_match:
                shard, realm, alias = alias_match.groups()
                return cls(
                    shard=int(shard),
                    realm=int(realm),
                    num=0,
                    alias_key=PublicKey.from_bytes(bytes.fromhex(alias))
                )
            
            raise ValueError(
                f"Invalid account ID string '{account_id_str}'. Expected format 'shard.realm.num'."
            ) from e

    @classmethod
    def _from_proto(cls, account_id_proto: basic_types_pb2.AccountID) -> "AccountId":
        """
        Creates an AccountId instance from a protobuf AccountID object.

        Args:
            account_id_proto (AccountID): The protobuf AccountID object.

        Returns:
            AccountId: An instance of AccountId.
        """
        result = cls(
            shard=account_id_proto.shardNum,
            realm=account_id_proto.realmNum,
            num=account_id_proto.accountNum,
        )
        if account_id_proto.alias:
            alias = account_id_proto.alias[2:]  # remove 0x prefix
            result.alias_key = PublicKey.from_bytes(alias)
        return result

    def _to_proto(self) -> basic_types_pb2.AccountID:
        """
        Converts the AccountId instance to a protobuf AccountID object.

        Returns:
            AccountID: The protobuf AccountID object.
        """
        account_id_proto = basic_types_pb2.AccountID(
            shardNum=self.shard,
            realmNum=self.realm,
            accountNum=self.num,
        )

        if self.alias_key:
            key = self.alias_key._to_proto().SerializeToString()
            account_id_proto.alias = key

        return account_id_proto

    @property
    def checksum(self) -> str | None:
        """Checksum of the accountId"""
        return self.__checksum

    def validate_checksum(self, client: "Client") -> None:
        """Validate the checksum for the accountId"""
        if self.alias_key is not None:
            raise ValueError("Cannot calculate checksum with an account ID that has a aliasKey")

        validate_checksum(
            self.shard,
            self.realm,
            self.num,
            self.__checksum,
            client,
        )

    def __str__(self) -> str:
        """
        Returns the string representation of the AccountId in 'shard.realm.num' format.
        """
        if self.alias_key:
            return f"{self.shard}.{self.realm}.{self.alias_key.to_string()}"
        return f"{self.shard}.{self.realm}.{self.num}"

    def to_string_with_checksum(self, client: "Client") -> str:
        """
        Returns the string representation of the AccountId with checksum 
        in 'shard.realm.num-checksum' format.
        """
        if self.alias_key is not None:
            raise ValueError("Cannot calculate checksum with an account ID that has a aliasKey")

        return format_to_string_with_checksum(
            self.shard,
            self.realm,
            self.num,
            client
        )

    def __repr__(self):
        """
        Returns the repr representation of the AccountId.
        """
        if self.alias_key:
            return (
                f"AccountId(shard={self.shard}, realm={self.realm}, "
                f"alias_key={self.alias_key.to_string_raw()})"
            )
        return f"AccountId(shard={self.shard}, realm={self.realm}, num={self.num})"

    def __eq__(self, other: object) -> bool:
        """
        Checks equality between two AccountId instances.
        Args:
            other (object): The object to compare with.
        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, AccountId):
            return False
        return (self.shard, self.realm, self.num, self.alias_key) == (
            other.shard,
            other.realm,
            other.num,
            other.alias_key,
        )

    def __hash__(self) -> int:
        """Returns a hash value for the AccountId instance."""
        return hash((self.shard, self.realm, self.num, self.alias_key))
