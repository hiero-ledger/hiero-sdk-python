from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2

class TokenNftTransfer:
    """
    Represents a transfer of a non-fungible token (NFT) from one account to another.
    
    This class encapsulates the details of an NFT transfer, including the sender,
    receiver, serial number of the NFT, and whether the transfer is approved.
    """
    
    def __init__(
        self,
        sender_id: AccountId,
        receiver_id: AccountId,
        serial_number: int,
        is_approved: bool = False
    ) -> None:
        """
        Initializes a new TokenNftTransfer instance.
        
        Args:
            sender_id (AccountId): The account ID of the sender.
            receiver_id (AccountId): The account ID of the receiver.
            serial_number (int): The serial number of the NFT being transferred.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
        """
        self.sender_id: AccountId = sender_id
        self.receiver_id: AccountId = receiver_id
        self.serial_number: int = serial_number
        self.is_approved: bool = is_approved
        
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
    def _from_proto(cls, proto: basic_types_pb2.NftTransfer):
        """
        Creates a TokenNftTransfer from a protobuf representation.
        """
        return cls(
            sender_id=AccountId._from_proto(proto.senderAccountID),
            receiver_id=AccountId._from_proto(proto.receiverAccountID),
            serial_number=proto.serialNumber,
            is_approved=proto.is_approval
        )

    def __str__(self):
        """
        Returns a string representation of this TokenNftTransfer instance.
        
        Returns:
            str: A string representation of this NFT transfer.
        """
        return f"TokenNftTransfer(sender_id={self.sender_id}, receiver_id={self.receiver_id}, serial_number={self.serial_number}, is_approved={self.is_approved})"
