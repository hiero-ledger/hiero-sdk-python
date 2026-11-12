"""
hiero_sdk_python.tokens.token_nft_transfer.py.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenNftTransfer for representing and converting NFT transfer details
(sender, receiver, serial number, approval) to and from protobuf messages.
"""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.nft_hook_call import NftHookCall
from hiero_sdk_python.tokens.token_id import TokenId


class TokenNftTransfer:
    """
    Represents a transfer of a non-fungible token (NFT) from one account to another.

    This class encapsulates the details of an NFT transfer, including the sender,
    receiver, serial number of the NFT, and whether the transfer is approved.
    """

    def __init__(
        self,
        token_id: TokenId,
        sender_id: AccountId,
        receiver_id: AccountId,
        serial_number: int,
        is_approved: bool = False,
        sender_hook_call: NftHookCall | None = None,
        receiver_hook_call: NftHookCall | None = None,
    ) -> None:
        """
        Initializes a new TokenNftTransfer instance.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            sender_id (AccountId): The account ID of the sender.
            receiver_id (AccountId): The account ID of the receiver.
            serial_number (int): The serial number of the NFT being transferred.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
            sender_hook_call (NftHookCall, optional): The sender's account allowance
                hook to call (HIP-1195). Its type must be a sender type.
            receiver_hook_call (NftHookCall, optional): The receiver's account allowance
                hook to call (HIP-1195). Its type must be a receiver type.
        """
        self.token_id: TokenId = token_id
        self.sender_id: AccountId = sender_id
        self.receiver_id: AccountId = receiver_id
        self.serial_number: int = serial_number
        self.is_approved: bool = is_approved
        self.sender_hook_call: NftHookCall | None = sender_hook_call
        self.receiver_hook_call: NftHookCall | None = receiver_hook_call

    def _to_proto(self) -> basic_types_pb2.NftTransfer:
        """
        Converts this TokenNftTransfer instance to its protobuf representation.

        Returns:
            basic_type_pb2.NftTransfer: The protobuf representation of this NFT transfer.

        Raises:
            ValueError: If a hook call has the wrong side's type, or if both
                is_approved and a sender hook call are set.
        """
        proto = basic_types_pb2.NftTransfer(
            senderAccountID=self.sender_id._to_proto(),
            receiverAccountID=self.receiver_id._to_proto(),
            serialNumber=self.serial_number,
            is_approval=self.is_approved,
        )
        if self.sender_hook_call is not None:
            if not self.sender_hook_call.hook_type.is_sender:
                raise ValueError("sender_hook_call must use a sender NftHookType.")
            if self.is_approved:
                raise ValueError("An approved NFT transfer cannot also call the sender's allowance hook.")
            self.sender_hook_call._apply_to(proto)
        if self.receiver_hook_call is not None:
            if not self.receiver_hook_call.hook_type.is_receiver:
                raise ValueError("receiver_hook_call must use a receiver NftHookType.")
            self.receiver_hook_call._apply_to(proto)
        return proto

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.TokenTransferList):
        """Creates a TokenNftTransfer from a protobuf representation."""
        token_id = TokenId._from_proto(proto.token)
        return [cls._from_nft_transfer_proto(token_id, nft_transfer) for nft_transfer in proto.nftTransfers]

    @classmethod
    def _from_nft_transfer_proto(cls, token_id: TokenId, proto: basic_types_pb2.NftTransfer) -> TokenNftTransfer:
        """Creates a TokenNftTransfer for the given token from an NftTransfer protobuf."""
        sender_hook_call, receiver_hook_call = NftHookCall._from_nft_transfer(proto)
        return cls(
            token_id=token_id,
            sender_id=AccountId._from_proto(proto.senderAccountID),
            receiver_id=AccountId._from_proto(proto.receiverAccountID),
            serial_number=proto.serialNumber,
            is_approved=proto.is_approval,
            sender_hook_call=sender_hook_call,
            receiver_hook_call=receiver_hook_call,
        )

    def __str__(self):
        """
        Returns a string representation of this TokenNftTransfer instance.

        Returns:
            str: A string representation of this NFT transfer.
        """
        return (
            "TokenNftTransfer("
            f"token={self.token_id}, "
            f"sender_id={self.sender_id}, "
            f"receiver_id={self.receiver_id}, "
            f"serial_number={self.serial_number}, "
            f"is_approved={self.is_approved}"
            f"{f', sender_hook_call={self.sender_hook_call}' if self.sender_hook_call is not None else ''}"
            f"{f', receiver_hook_call={self.receiver_hook_call}' if self.receiver_hook_call is not None else ''}"
            ")"
        )
