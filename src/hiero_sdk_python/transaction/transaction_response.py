"""
transaction_response.py
~~~~~~~~~~~~~~~~~~~~~~~~

Represents the response from a transaction submitted to the Hedera network.
Provides methods to retrieve the receipt and access core transaction details.
"""
from typing import Optional, Union
from typing import TYPE_CHECKING

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord

if TYPE_CHECKING:
    from hiero_sdk_python.transaction.transaction import Transaction

# pylint: disable=too-few-public-methods

class TransactionResponse:
    """
    Represents the response from a transaction submitted to the network.
    """

    def __init__(self) -> None:
        """
        Initialize a new TransactionResponse instance with default values.
        """
        self.transaction_id: TransactionId = TransactionId()
        self.node_id: AccountId = AccountId()
        self.hash: bytes = bytes()
        self.validate_status: bool = False
        self.transaction: Optional["Transaction"] = None
    
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
    
    def get_receipt(self, client: "Client", timeout: Optional[Union[int, float]] = None) -> "TransactionReceipt":
        """
        Retrieves the receipt for this transaction from the network.

        Args:
            client (Client): The client instance to use for receipt retrieval.
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TransactionReceipt: The receipt from the network, containing the status
                               and any entities created by the transaction
        """
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
        )
    
    def get_record(self, client: "Client", timeout: Optional[Union[int, float]] = None) -> "TransactionRecord":
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
