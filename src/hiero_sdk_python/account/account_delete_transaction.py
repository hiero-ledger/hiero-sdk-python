"""
AccountDeleteTransaction class.
"""

from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.crypto_delete_pb2 import CryptoDeleteTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction

DEFAULT_TRANSACTION_FEE = Hbar(2).to_tinybars()


class AccountDeleteTransaction(Transaction):
    """
    A transaction that deletes a account.

    This transaction can be used to delete an existing account from the network.

    Args:
        account_id (Optional[AccountId]): The ID of the account to delete.
        transfer_account_id (Optional[AccountId]): The account ID to transfer
            remaining balance to.
    """

    def __init__(
        self,
        account_id: Optional[AccountId] = None,
        transfer_account_id: Optional[AccountId] = None,
    ):
        """
        Initializes a new AccountDeleteTransaction instance.

        Args:
            account_id (Optional[AccountId]): The ID of the account to delete.
            transfer_account_id (Optional[AccountId]): The account ID to transfer
                remaining balance to.
        """
        super().__init__()
        self.account_id: Optional[AccountId] = account_id
        self.transfer_account_id: Optional[AccountId] = transfer_account_id
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def set_account_id(
        self, account_id: Optional[AccountId]
    ) -> "AccountDeleteTransaction":
        """
        Sets the ID of the account to delete.

        Args:
            account_id (Optional[AccountId]): The ID of the account to delete.

        Returns:
            AccountDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_transfer_account_id(
        self, transfer_account_id: Optional[AccountId]
    ) -> "AccountDeleteTransaction":
        """
        Sets the account ID to transfer the remaining balance to.

        When an account is deleted, its remaining balance must be transferred
        to another account. This method sets the target account for the balance transfer.

        Args:
            transfer_account_id (Optional[AccountId]): The account ID to transfer
                remaining balance to.

        Returns:
            AccountDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.transfer_account_id = transfer_account_id
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the account delete transaction.

        Returns:
            CryptoDeleteTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If account_id or transfer_account_id is not set.
        """
        if self.account_id is None:
            raise ValueError("Missing required AccountID")

        if self.transfer_account_id is None:
            raise ValueError("Missing AccountID for transfer")

        return CryptoDeleteTransactionBody(
            deleteAccountID=self.account_id._to_proto(),
            transferAccountID=(
                self.transfer_account_id._to_proto()
                if self.transfer_account_id
                else None
            ),
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this account delete transaction.

        Returns:
            TransactionBody: The built transaction body.

        Raises:
            ValueError: If account_id or transfer_account_id is not set.
        """
        account_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoDelete.CopyFrom(account_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this account delete transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        account_delete_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.cryptoDelete.CopyFrom(account_delete_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the account delete transaction.

        Args:
            channel (_Channel): The channel containing service stubs.

        Returns:
            _Method: An object containing the transaction function to
                delete accounts.
        """
        return _Method(transaction_func=channel.crypto.cryptoDelete, query_func=None)
