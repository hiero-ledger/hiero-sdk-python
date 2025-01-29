import re
from dataclasses import dataclass
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId

@dataclass(frozen=True, init=True, repr=True, eq=True)
class NftId:
    """
    A unique identifiers for Non-Fungible Tokens (NFTs).
    The NftId has a TokenId, and a serial number.
    """

    tokenId: TokenId
    serialNumber: int

    def __post_init__(self):
        if self.tokenId is None:
            raise TypeError("token_id is required")
        if not isinstance(self.tokenId, TokenId):
            raise TypeError(f"token_id must be of type TokenId, got {type(self.tokenId)}")
        if not isinstance(self.serialNumber, int):
            raise TypeError(f"Expected an integer for serial_number, got {type(self.serialNumber)}")
        if self.serialNumber < 0:
            raise ValueError("serial_number must be positive")
        return True

    @classmethod
    def from_proto(cls, nft_id_proto:basic_types_pb2.NftID = None):
        """
        :param nft_id_proto: the proto NftID object
        :return: a NftId object
        """
        return cls(
            tokenId=TokenId.from_proto(nft_id_proto.token_ID),
            serialNumber=nft_id_proto.serial_number
        )

    def to_proto(self):
        """
        :return: a protobuf NftID object representation of this NftId object
        """
        nft_id_proto = basic_types_pb2.NftID(token_ID=self.tokenId.to_proto(), serial_number=self.serialNumber)

        return nft_id_proto

    @classmethod
    def from_string(cls, nft_id_str:str = ""):
        """
        :param nft_id_str: a string NftId representation
        :return: returns the NftId parsed from the string input
        """

        parts = re.split(r"/", nft_id_str)
        if len(parts) != 2:
            raise ValueError("nft_id_str must formatted as: shard.realm.number/serial_number")

        return cls(
            tokenId=TokenId.from_string(parts[0]),
            serialNumber=int(parts[1])
        )

    def __str__(self):
        """
        :return: a human-readable representation of the NftId
        """
        return f"{str(self.tokenId)}/{str(self.serialNumber)}"
