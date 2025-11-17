from typing import List, Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.transaction_pb2 import AtomicBatchTransactionBody
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


class BatchTransaction(Transaction):
    def __init__(self, transactions: Optional[List[Transaction]]=None) -> None:
        super().__init__()
        self.inner_transactions: List[Transaction] =  self.set_inner_transactions(transactions) if transactions else []

    def set_inner_transactions(self, transactions: List[Transaction]) -> "BatchTransaction":
        self._require_not_frozen()
        for transaction in transactions:
            self._verify_inner_transactions(transaction)

        self.inner_transactions = transactions
        return self

    def add_inner_transaction(self, transaction: Transaction) -> "BatchTransaction":
        self._require_not_frozen()
        self._verify_inner_transactions(transaction)
        self.inner_transactions.append(transaction)
        return self

    def get_inner_transactions_ids(self) -> List[TransactionId]:
        transaction_ids: List[TransactionId] = []
        for transaction in self.inner_transactions:
            transaction_ids.append(transaction.transaction_id)

        return transaction_ids

    def _verify_inner_transactions(self, transaction: Transaction) -> bool:
        if isinstance(transaction, (FreezeTransaction, BatchTransaction)):
            raise ValueError(f"Transaction type {type(transaction)} is not allowed in a batch transaction")

        if transaction._transaction_body_bytes is None:
            return ValueError("Transaction must be frozen")

        if transaction.batch_key is None:
            raise ValueError("Batch key needs to be set")

    def _build_proto_body(self) -> AtomicBatchTransactionBody:
        proto_body = AtomicBatchTransactionBody()
        for transaction in self.inner_transactions:
            proto_body.transactions.append(transaction._make_request().signedTransactionBytes)

        return proto_body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.atomic_batch.CopyFrom(self._build_proto_body())
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.util.atomicBatch,
            query_func=None
        )
