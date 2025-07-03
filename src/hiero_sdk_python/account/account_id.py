from hiero_sdk_python.hapi.services import basic_types_pb2

class AccountId:
    def __init__(self, shard=0, realm=0, num=0):
        self.shard = shard
        self.realm = realm
        self.num = num

    @classmethod
    def from_string(cls, account_id_str):
        """
        Creates an AccountId instance from a string in the format 'shard.realm.num'.
        """
        parts = account_id_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError("Invalid account ID string format. Expected 'shard.realm.num'")
        shard, realm, num = map(int, parts)
        return cls(shard, realm, num)

    @classmethod
    def _from_proto(cls, account_id_proto):
        """
        Creates an AccountId instance from a protobuf AccountID object.

        Args:
            account_id_proto (AccountID): The protobuf AccountID object.

        Returns:
            AccountId: An instance of AccountId.
        """
        return cls(
            shard=account_id_proto.shardNum,
            realm=account_id_proto.realmNum,
            num=account_id_proto.accountNum
        )

    def _to_proto(self):
        """
        Converts the AccountId instance to a protobuf AccountID object.

        Returns:
            AccountID: The protobuf AccountID object.
        """
        return basic_types_pb2.AccountID(
            shardNum=self.shard,
            realmNum=self.realm,
            accountNum=self.num
        )

    def __str__(self):
        """
        Returns the string representation of the AccountId in 'shard.realm.num' format.
        """
        return f"{self.shard}.{self.realm}.{self.num}"

    def __repr__(self):
        """
        Returns the repr representation of the AccountId.
        """
        return f"AccountId(shard={self.shard}, realm={self.realm}, num={self.num})"

    def __eq__(self, other):
            if not isinstance(other, AccountId):
                return False
            return (self.shard, self.realm, self.num) == (other.shard, other.realm, other.num)

    def __hash__(self):
        return hash((self.shard, self.realm, self.num))