"""
transaction_response.py.
~~~~~~~~~~~~~~~~~~~~~~~~

Represents the response from a transaction submitted to the Hedera network.
Provides methods to retrieve the receipt and access core transaction details.
"""

from __future__ import annotations

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
    """Represents the response from a transaction submitted to the network."""

    def __init__(self) -> None:
        """Initialize a new TransactionResponse instance with default values."""
        self.transaction_id: TransactionId = TransactionId()
        self.node_id: AccountId = AccountId()
        self.hash: bytes = b""
        self.validate_status: bool = False
        self.transaction: Transaction | None = None
        self._transaction_node_ids: list[AccountId] | None = None

    def get_receipt_query(self, validate_status: bool = False, client: Client | None = None):
        """
        Create a receipt query for this transaction.

        Args:
            validate_status (bool, optional): The query should automatically validate the transaction status. (default False)
            client (Client, optional): The client to enable failover behavior.

        Returns:
            TransactionGetReceiptQuery: A configured receipt query.

        Raises:
            TypeError: If `validate_status` is not a bool or `client` is not a Client.
        """
        from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery

        if not isinstance(validate_status, bool):
            raise TypeError("validate_status must be a boolean")

        if client is not None and not isinstance(client, Client):
            raise TypeError("client must be an instance of Client")

        node_account_ids = self._resolve_node_account_ids(client)
        return (
            TransactionGetReceiptQuery()
            .set_transaction_id(self.transaction_id)
            .set_node_account_ids(node_account_ids)
            .set_validate_status(validate_status)
        )

    def get_receipt(
        self, client: Client, timeout: int | float | None = None, validate_status: bool = False
    ) -> TransactionReceipt:
        """
        Retrieves the receipt for this transaction from the network.

        Args:
            client (Client): The client instance to use for receipt retrieval.
            timeout (int | float, optional): The total execution timeout (in seconds) for this execution.
            validate_status (bool, optional): The query should automatically validate the transaction status. (default False)

        Returns:
            TransactionReceipt: The receipt from the network, containing the status
                               and any entities created by the transaction
        """
        return self.get_receipt_query(validate_status=validate_status, client=client).execute(client, timeout)

    def get_record_query(self, client: Client | None = None):
        """
        Create a record query for this transaction.

        Args:
            client (Client, optional): The client to enable failover behavior.

        Returns:
            TransactionRecordQuery: A configured record query.

        Raises:
            TypeError: If `client` is not a Client.
        """
        from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery

        if client is not None and not isinstance(client, Client):
            raise TypeError("client must be an instance of Client")

        node_account_ids = self._resolve_node_account_ids(client)
        return TransactionRecordQuery().set_transaction_id(self.transaction_id).set_node_account_ids(node_account_ids)

    def get_record(self, client: Client, timeout: int | float | None = None) -> TransactionRecord:
        """
        Retrieve the transaction record from the network.

        Args:
            client (Client): The client instance used to execute the query.
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TransactionRecord: The full transaction record.
        """
        return self.get_record_query(client).execute(client, timeout)

    def _resolve_node_account_ids(self, client: Client) -> list[AccountId]:
        """Resolve node account IDs for receipt or record query failover."""
        node_account_ids = [self.node_id]

        if client is None or not client.allow_receipt_node_failover:
            return node_account_ids

        available_node_ids = self._transaction_node_ids if self._transaction_node_ids else client.get_node_account_ids()
        node_account_ids.extend(node_id for node_id in available_node_ids if node_id != self.node_id)
        return node_account_ids
