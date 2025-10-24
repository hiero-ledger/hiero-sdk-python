"""
hiero_sdk_python.tokens.token_nft_transfer.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenNftTransfer for representing and converting NFT transfer details
(sender, receiver, serial number, approval) to and from protobuf messages.
"""
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
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
        is_approved: bool = False
    ) -> None:
        """
        Initializes a new TokenNftTransfer instance.
        
        Args:
            token_id (TokenId): The ID of the token being transferred.
            sender_id (AccountId): The account ID of the sender.
            receiver_id (AccountId): The account ID of the receiver.
            serial_number (int): The serial number of the NFT being transferred.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
        """
        self.token_id: TokenId = token_id
        self.sender_id : AccountId = sender_id
        self.receiver_id : AccountId = receiver_id
        self.serial_number : int = serial_number
        self.is_approved : bool = is_approved

    def _to_proto(self) -> basic_types_pb2.NftTransfer:
        """
        Converts this TokenNftTransfer instance to its protobuf representation.
        
        Returns:
            basic_type_pb2.NftTransfer: The protobuf representation of this NFT transfer.
        """
        return basic_types_pb2.NftTransfer(
            senderAccountID=self.sender_id._to_proto(),
            receiverAccountID=self.receiver_id._to_proto(),
            serialNumber=self.serial_number,
            is_approval=self.is_approved
        )

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.TokenTransferList):
        """
        Creates a TokenNftTransfer from a protobuf representation.
        """
        nftTransfers: list[TokenNftTransfer] = []

        token_id = TokenId._from_proto(proto.token)
        for nftTransfer in proto.nftTransfers:
            nftTransfers.append(
                cls(
                    token_id = token_id,
                    sender_id=AccountId._from_proto(nftTransfer.senderAccountID),
                    receiver_id=AccountId._from_proto(nftTransfer.receiverAccountID),
                    serial_number=nftTransfer.serialNumber,
                    is_approved=nftTransfer.is_approval
                )
            )

        return nftTransfers

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
            ")"
        )
