"""
hiero_sdk_python.transaction.batch_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the BatchTransaction class — a subclass of Transaction that enables
grouping multiple frozen, signed transactions (with batch keys) into a single
atomic operation on the Hedera network.
"""
from typing import List, Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.transaction_pb2 import AtomicBatchTransactionBody
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId

class BatchTransaction(Transaction):
    """
    Represents an atomic batch transaction on the Hedera network.
    """
    def __init__(self, inner_transactions: Optional[List[Transaction]]=None) -> None:
        """
        Initialize a new BatchTransaction.

        Args:
            inner_transactions (Optional[List[Transaction]]):
                An optional list of transactions to include in the batch.
        """
        super().__init__()
        self.inner_transactions: List[Transaction] = []

        if inner_transactions:
            self.set_inner_transactions(inner_transactions)

    def set_inner_transactions(self, transactions: List[Transaction]) -> "BatchTransaction":
        """
        Set the inner_transaction for batch transaction.

        Args:
            transactions (List[Transaction]): 
                A list of frozen transactions with a batch key already set.
        
        Returns:
           BatchTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        for transaction in transactions:
            self._verify_inner_transaction(transaction)

        self.inner_transactions = transactions
        return self

    def add_inner_transaction(self, transaction: Transaction) -> "BatchTransaction":
        """
        Add the inner_transaction for batch transaction.

        Args:
            transaction (Transaction): 
                A frozen transaction with a batch key.
        
        Returns:
           BatchTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self._verify_inner_transaction(transaction)
        self.inner_transactions.append(transaction)
        return self

    def get_inner_transaction_ids(self) -> List[TransactionId]:
        """
        Retrieve the TransactionIds of all inner batch transactions.

        Returns:
            List[TransactionId]: IDs of all included transactions.
        """
        transaction_ids: List[TransactionId] = []
        for transaction in self.inner_transactions:
            transaction_ids.append(transaction.transaction_id)

        return transaction_ids

    def _verify_inner_transaction(self, transaction: Transaction) -> None:
        """
        Validate that a transaction can be included as an inner batch transaction.

        Raises:
            ValueError: If the transaction is invalid for batching.
        """
        if isinstance(transaction, (FreezeTransaction, BatchTransaction)):
            raise ValueError(
                f"Transaction type {type(transaction).__name__} "
                "is not allowed in a batch transaction"
            )

        if not transaction._transaction_body_bytes:
            raise ValueError("Transaction must be frozen")

        if transaction.batch_key is None:
            raise ValueError("Batch key needs to be set")

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map) -> "BatchTransaction":
        """
        Creates a BatchTransaction instance from protobuf components.

        Args:
            transaction_body: The parsed TransactionBody protobuf
            body_bytes (bytes): The raw bytes of the transaction body
            sig_map: The SignatureMap protobuf containing signatures

        Returns:
            BatchTransaction: A new transaction instance with all fields restored
        """
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)

        if transaction_body.HasField('atomic_batch'):
            atomic_batch = transaction_body.atomic_batch

            for inner_transaction in atomic_batch.transactions:
                inner_tx_proto = transaction_pb2.Transaction(
                    signedTransactionBytes=inner_transaction
                )

                transaction.inner_transactions.append(
                    Transaction.from_bytes(inner_tx_proto.SerializeToString())
                )

        return transaction

    def _build_proto_body(self) -> AtomicBatchTransactionBody:
        """
        Returns the protobuf body for the batch transaction.
        """
        if len(self.inner_transactions) == 0:
            raise ValueError("BatchTransaction requires at least one inner transaction.")

        proto_body = AtomicBatchTransactionBody()
        for transaction in self.inner_transactions:
            proto_body.transactions.append(transaction._make_request().signedTransactionBytes)

        return proto_body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for a batch transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.atomic_batch.CopyFrom(self._build_proto_body())
        return transaction_body

    def build_scheduled_body(self):
        """Batch transactions cannot be scheduled."""
        raise ValueError("Cannot schedule Atomic Batch transaction.")

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.util.atomicBatch,
            query_func=None
        )
