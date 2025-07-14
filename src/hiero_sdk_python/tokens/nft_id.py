"""
nft_id.py

Defines NftId, a value object for representing and validating a unique
Non-Fungible Token (NFT) identifier, including conversion to/from
Protobuf and string serialization.
"""
import re
import warnings

from dataclasses import dataclass
from typing import Optional
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId

@dataclass(frozen=True)
class NftId:
    """
    A unique identifier for Non-Fungible Tokens (NFTs).
    The NftId has a TokenId and a serial number.
    """

    token_id: TokenId
    serial_number: int

    # Legacy aliases for backward compatibility - will be depreciated
    @property
    def tokenId(self) -> TokenId:
        warnings.warn(
            "NftId.tokenId is deprecated; use NftId.token_id",
            FutureWarning,
            stacklevel=2,
        )
        return self.token_id

    @property
    def serialNumber(self) -> int:
        """Legacy alias for serial_number (deprecated)."""
        warnings.warn(
            "NftId.serialNumber is deprecated; use NftId.serial_number",
            FutureWarning,
            stacklevel=2,
        )
        return self.serial_number

    def __post_init__(self) -> None:
        """Validate the NftId after initialization."""
        if self.token_id is None:
            raise TypeError("token_id is required")
        if not isinstance(self.token_id, TokenId):
            raise TypeError(f"token_id must be of type TokenId, got {type(self.token_id)}")
        if not isinstance(self.serial_number, int):
            raise TypeError(f"serial_number must be an integer, got {type(self.serial_number)}")
        if self.serial_number < 0:
            raise ValueError("serial_number must be non-negative")

    @classmethod
    def _from_proto(cls, nft_id_proto: Optional[basic_types_pb2.NftID] = None) -> "NftId":
        """
        :param nft_id_proto: the proto NftID object
        :return: an NftId object
        """
        if nft_id_proto is None:
            raise ValueError("nft_id_proto is required")
        return cls(
            token_id=TokenId._from_proto(nft_id_proto.token_ID),
            serial_number=nft_id_proto.serial_number,
        )

    def _to_proto(self) -> basic_types_pb2.NftID:
        """
        :return: a protobuf NftID object representation of this NftId object
        """
        nft_id_proto = basic_types_pb2.NftID(
            token_ID=self.token_id._to_proto(),
            serial_number=self.serial_number,
        )
        return nft_id_proto

    @classmethod
    def from_string(cls, nft_id_str: str) -> "NftId":
        """
        :param nft_id_str: a string NftId representation
        :return: returns the NftId parsed from the string input
        """
        parts = re.split(r"/", nft_id_str)
        if len(parts) != 2:
            raise ValueError(
                "nft_id_str must be formatted as: shard.realm.number/serial_number"
            )
        token_part, serial_part = parts
        return cls(
            token_id=TokenId.from_string(token_part),
            serial_number=int(serial_part),
        )

    def __str__(self) -> str:
        """
        :return: a human-readable representation of the NftId
        """
        return f"{self.token_id}/{self.serial_number}"
