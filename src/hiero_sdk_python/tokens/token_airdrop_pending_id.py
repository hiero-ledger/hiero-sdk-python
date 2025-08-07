"""
PendingAirdropId module.

Defines the PendingAirdropId class used to uniquely identify a specific pending token airdrop.

A PendingAirdropId acts as a reference to a single unclaimed token or NFT transfer, 
typically created by an airdrop transaction. It is required when constructing a 
TokenClaimAirdropTransaction to finalize and receive the associated asset.

This class supports safe construction, validation, and conversion to/from protobuf 
for use within the Hiero SDK.
"""

from dataclasses import dataclass
from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId

@dataclass(frozen=True)
class PendingAirdropId:
    """
    Represents a pending airdrop id, containing sender_id and receiver_id of an airdrop, along with
    the specific token being airdropped.
      which can be either a fungible_token_id (TokenId) or a nft_id (NftId).
    """
    sender_id: AccountId
    receiver_id: AccountId
    token_id: Optional[TokenId] = None
    nft_id: Optional[NftId] = None

    def __post_init__(self):
        if self.sender_id is None:
            raise TypeError("sender_id must not be None")
        if self.receiver_id is None:
            raise TypeError("receiver_id must not be None")
        if (self.token_id is None) == (self.nft_id is None):
            raise ValueError("Exactly one of token_id or nft_id must be set.")

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.PendingAirdropId) -> "PendingAirdropId":
        """
        Create a PendingAirdropId instance from protobuf message.
        Ensures only one token type is present.

        Args:
            proto (basic_types_pb2.PendingAirdropId): 
            The protobuf message containing PendingAirdropId information.

        Returns:
            PendingAirdropId: A new PendingAirdropId instance populated from the protobuf message.
        """
        has_fungible = proto.HasField("fungible_token_type")
        has_nft = proto.HasField("non_fungible_token")

        if has_fungible and has_nft:
            raise ValueError("Protobuf contains both token types, only one is allowed.")
        if not has_fungible and not has_nft:
            raise ValueError("Protobuf contains neither token type.")

        # Return if there is one token type
        return cls(
            sender_id=AccountId._from_proto(proto.sender_id),
            receiver_id=AccountId._from_proto(proto.receiver_id),
            token_id=TokenId._from_proto(proto.fungible_token_type) if has_fungible else None,
            nft_id=NftId._from_proto(proto.non_fungible_token) if has_nft else None
        )

    def _to_proto(self) -> basic_types_pb2.PendingAirdropId:
        """
        Converts this PendingAirdropId instance to its protobuf representation.
        Only one token type will be set.

        Returns:
            basic_types_pb2.PendingAirdropId: The protobuf representation of the PendingAirdropId.
        """
        if self.token_id:
            return basic_types_pb2.PendingAirdropId(
                sender_id=self.sender_id._to_proto(),
                receiver_id=self.receiver_id._to_proto(),
                fungible_token_type=self.token_id._to_proto()
            )
        if self.nft_id:
            return basic_types_pb2.PendingAirdropId(
                sender_id=self.sender_id._to_proto(),
                receiver_id=self.receiver_id._to_proto(),
                non_fungible_token=self.nft_id._to_proto()
            )
        raise RuntimeError("PendingAirdropId must have a token or NFT set.")

    def __str__(self) -> str:
        """
        Returns a string representation of this PendingAirdropId instance.
        """
        asset = self.token_id or self.nft_id
        token_type = "TokenId" if self.token_id else "NftId"
        return (
            f"PendingAirdropId("
            f"sender_id={self.sender_id}, "
            f"receiver_id={self.receiver_id}, "
            f"{token_type}={asset})"
        )
