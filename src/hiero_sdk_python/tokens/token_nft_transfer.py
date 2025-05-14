from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2

class _TokenNftTransfer:
    def __init__(self, sender_id, receiver_id, serial_number, is_approved=False):
        self.sender_id : AccountId = sender_id
        self.receiver_id : AccountId = receiver_id
        self.serial_number : int = serial_number
        self.is_approved : bool = is_approved
        
    def to_proto(self):
        return basic_types_pb2.NftTransfer(
            senderAccountID=self.sender_id.to_proto(),
            receiverAccountID=self.receiver_id.to_proto(),
            serialNumber=self.serial_number,
            is_approval=self.is_approved
        )
    
    def __str__(self):
        return f"TokenNftTransfer(sender_id={self.sender_id}, receiver_id={self.receiver_id}, serial_number={self.serial_number}, is_approved={self.is_approved})"
