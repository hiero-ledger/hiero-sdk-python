from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_record_pb2
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId


class PendingAirdropRecord:
    """
    Represents a record of a pending airdrop, retrieved from a transaction.
    """
    def __init__(self, pending_airdrop_id: PendingAirdropId, amount: int) -> None:
        """
        Initializes a new PendingAirdropRecord.

        Args:
            pending_airdrop_id: The ID of pending airdrop.
            amount: The amount of tokens associated with this pending airdrop.
        """
        self.pending_airdrop_id = pending_airdrop_id
        self.amount = amount
    
    @classmethod
    def _from_proto(cls, proto: transaction_record_pb2.PendingAirdropRecord) -> "PendingAirdropRecord":
        """
        Creates a PendingAirdropRecord instance from a protobuf message.

        Args:
            proto: The protobuf message of PendingAirdropRecord.

        Returns:
            PendingAirdropRecord: A new instance of PendingAirdropRecord.
        """
        return cls(
            pending_airdrop_id=PendingAirdropId._from_proto(proto.pending_airdrop_id),
            amount=proto.pending_airdrop_value.amount
        )
    
    def _to_proto(self) -> transaction_record_pb2.PendingAirdropRecord:
        """
        Converts the PendingAirdropRecord instance to its protobuf message.

        Returns: 
            transaction_record_pb2.PendingAirdropRecord: The protobuf representation of the PendingAirdropRecord.

        """
        return transaction_record_pb2.PendingAirdropRecord(
            pending_airdrop_id=self.pending_airdrop_id._to_proto(),
            pending_airdrop_value=basic_types_pb2.PendingAirdropValue(amount=self.amount)
        )
    
    def __str__(self):
        """
        Returns a string representation of this PendingAirdropRecord instance.
        """
        return f"PendingAirdropRecord(pending_airdrop_id={self.pending_airdrop_id}, amount={self.amount})"