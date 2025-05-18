from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2

class TokenNftTransfer:
    """
    Represents a transfer of a non-fungible token (NFT) from one account to another.
    
    This class encapsulates the details of an NFT transfer, including the sender,
    receiver, serial number of the NFT, and whether the transfer is approved.
    """
    
    def __init__(self, sender_id, receiver_id, serial_number, is_approved=False):
        """
        Initializes a new TokenNftTransfer instance.
        
        Args:
            sender_id (AccountId): The account ID of the sender.
            receiver_id (AccountId): The account ID of the receiver.
            serial_number (int): The serial number of the NFT being transferred.
            is_approved (bool, optional): Whether the transfer is approved. Defaults to False.
        """
        self.sender_id : AccountId = sender_id
        self.receiver_id : AccountId = receiver_id
        self.serial_number : int = serial_number
        self.is_approved : bool = is_approved
        
    def to_proto(self):
        """
        Converts this TokenNftTransfer instance to its protobuf representation.
        
        Returns:
            NftTransfer: The protobuf representation of this NFT transfer.
        """
        return basic_types_pb2.NftTransfer(
            senderAccountID=self.sender_id.to_proto(),
            receiverAccountID=self.receiver_id.to_proto(),
            serialNumber=self.serial_number,
            is_approval=self.is_approved
        )
    
    def __str__(self):
        """
        Returns a string representation of this TokenNftTransfer instance.
        
        Returns:
            str: A string representation of this NFT transfer.
        """
        return f"TokenNftTransfer(sender_id={self.sender_id}, receiver_id={self.receiver_id}, serial_number={self.serial_number}, is_approved={self.is_approved})"
