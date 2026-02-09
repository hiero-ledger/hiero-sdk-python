"""
transaction_response.py
~~~~~~~~~~~~~~~~~~~~~~~~

Represents the response from a transaction submitted to the Hedera network.
Provides methods to retrieve the receipt and access core transaction details.
"""
from multiprocessing.connection import Client
from typing import Optional, Union
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction_id import TransactionId
# pylint: disable=too-few-public-methods

class TransactionResponse:
    """
    Represents the response from a transaction submitted to the Hedera network.
    """

    def __init__(self) -> None:
        """
        Initialize a new TransactionResponse instance with default values.
        """
        self.transaction_id = TransactionId()
        self.node_id: AccountId = AccountId()
        self.hash: bytes = bytes()
        self.validate_status: bool = False
        self.transaction = None
    
    def get_receipt_query(self):
        """
        Create a receipt query for this transaction.

        Returns:
            TransactionGetReceiptQuery: A configured receipt query.
        """
        from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
        return (
            TransactionGetReceiptQuery()
            .set_transaction_id(self.transaction_id)
            .set_node_account_id(self.node_id)
        )
    
    def get_receipt(self, client: Client, timeout: Optional[Union[int, float]] = None):
        """
        Retrieves the receipt for this transaction from the Hedera network.

        Args:
            client (Client): The client instance to use for receipt retrieval.
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TransactionReceipt: The receipt from the network, containing the status
                               and any entities created by the transaction
        """
        # TODO: Decide how to avoid circular imports
        from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
        receipt = (
            TransactionGetReceiptQuery()
        receipt = self.get_receipt_query().execute(client)
        receipt = self.get_receipt_query().execute(client, timeout)
        return receipt
    
    def get_record_query(self):
        """
        Create a record query for this transaction.

        Returns:
            TransactionRecordQuery: A configured record query.
        """
        from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
        return (
            TransactionRecordQuery()
            .set_transaction_id(self.transaction_id)
            .set_node_account_ids([self.node_id])
            .execute(client)
            .set_node_account_id(self.node_id)
        )
    
    def get_record(self, client: Client, timeout: Optional[Union[int, float]] = None):
        """
        Retrieve the transaction record from the Hedera network.

        Args:
            client (Client): The client instance used to execute the query.
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TransactionRecord: The full transaction record.
        """
        record = self.get_record_query().execute(client, timeout)
        return record
