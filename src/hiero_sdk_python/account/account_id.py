from typing import List

from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2


class AccountId:
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

    @classmethod
    def from_string(cls, account_id_str: str) -> "AccountId":
        """
        Creates an AccountId instance from a string in the format 'shard.realm.num'.
        """
        parts: List[str] = account_id_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError(
                "Invalid account ID string format. Expected 'shard.realm.num'"
            )
        shard, realm, num = map(int, parts)
        return cls(shard, realm, num)

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
            result.alias_key = PublicKey.from_bytes(account_id_proto.alias)
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

    def __str__(self) -> str:
        """
        Returns the string representation of the AccountId in 'shard.realm.num' format.
        """
        if self.alias_key:
            return f"{self.shard}.{self.realm}.{self.alias_key.to_string()}"
        return f"{self.shard}.{self.realm}.{self.num}"

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
        return (self.shard, self.realm, self.num) == (
            other.shard,
            other.realm,
            other.num,
        )

    def __hash__(self) -> int:
        """Returns a hash value for the AccountId instance."""
        return hash((self.shard, self.realm, self.num))
