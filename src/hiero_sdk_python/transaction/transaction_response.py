from typing import TYPE_CHECKING

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction_id import TransactionId

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client


class TransactionResponse:
    """
    Represents the response from a transaction submitted to the Hedera network.
    """

    def __init__(self):
        """
        Initialize a new TransactionResponse instance with default values.
        """
        self.transaction_id = TransactionId()
        self.node_id = AccountId()
        self.hash = bytes()
        self.validate_status = False
        self.transaction = None

    def get_receipt(self, client: "Client"):
        """
        Retrieves the receipt for this transaction from the Hedera network.

        Args:
            client (Client): The client instance to use for receipt retrieval

        Returns:
            TransactionReceipt: The receipt from the network, containing the status
                               and any entities created by the transaction
        """
        receipt = client.get_transaction_receipt(self.transaction_id)
        return receipt
