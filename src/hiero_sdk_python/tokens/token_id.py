from hiero_sdk_python.hapi.services import basic_types_pb2

class TokenId:
    def __init__(self, shard=0, realm=0, num=0):
        self.shard = shard
        self.realm = realm
        self.num = num

    @classmethod
    def from_proto(cls, token_id_proto):
        """
        Creates a TokenId instance from a protobuf TokenID object.
        """
        return cls(
            shard=token_id_proto.shardNum,
            realm=token_id_proto.realmNum,
            num=token_id_proto.tokenNum
        )

    def to_proto(self):
        """
        Converts the TokenId instance to a protobuf TokenID object.
        """
        token_id_proto = basic_types_pb2.TokenID()
        token_id_proto.shardNum = self.shard
        token_id_proto.realmNum = self.realm
        token_id_proto.tokenNum = self.num
        return token_id_proto

    def __str__(self):
        """
        Returns the string representation of the TokenId in the format 'shard.realm.num'.
        """
        return f"{self.shard}.{self.realm}.{self.num}"

    @classmethod
    def from_string(cls, token_id_str):
        """
        Parses a string in the format 'shard.realm.num' to create a TokenId instance.
        """
        parts = token_id_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError("Invalid TokenId format. Expected 'shard.realm.num'")
        return cls(shard=int(parts[0]), realm=int(parts[1]), num=int(parts[2]))

    def __eq__(self, other):
        return self.shard == other.shard and self.realm == other.realm and self.num == other.num