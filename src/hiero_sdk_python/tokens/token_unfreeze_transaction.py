"""
hiero_sdk_python.transaction.token_unfreeze_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenUnfreezeTransaction, a subclass of Transaction for unfreezing tokens
on the Hedera network via the Hedera Token Service (HTS) API.
"""
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_unfreeze_account_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenUnfreezeTransaction(Transaction):
    """
    Represents a token unfreeze transaction on the Hedera network.
    
    This transaction unfreezes specified tokens for a given account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token unfreeze transaction.
    """

    def __init__(self, account_id=None, token_id=None):
        """
        Initializes a new TokenUnfreezeTransaction instance with default values.
        """
        super().__init__()
        self.token_id = token_id
        self.account_id = account_id
        self._default_transaction_fee = 3_000_000_000
        self._is_frozen = False

    def set_token_id(self, token_id):
        """Set the token ID to unfreeze."""
        self.__require_not_frozen()
        self.token_id = token_id
        return self

    def set_account_id(self, account_id):
        """Set the account ID whose token will be unfrozen."""
        self.__require_not_frozen()
        self.account_id = account_id
        return self

    def __require_not_frozen(self):
        if self._is_frozen:
            raise ValueError("Transaction is already frozen and cannot be modified.")

    def _build_proto_body(self):
        """
        Returns the protobuf body for the token unfreeze transaction.
        
        Returns:
            TokenUnfreezeAccountTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If account ID or token ID is not set.
        """
        if not self.token_id:
            raise ValueError("Missing required TokenID.")

        if not self.account_id:
            raise ValueError("Missing required AccountID.")

        return token_unfreeze_account_pb2.TokenUnfreezeAccountTransactionBody(
            account=self.account_id._to_proto(),
            token=self.token_id._to_proto()
        )
        
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token unfreeze.

        Returns:
            TransactionBody: The protobuf transaction body containing the token unfreeze details.
        """
        token_unfreeze_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenUnfreeze.CopyFrom(token_unfreeze_body)
        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token unfreeze transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_unfreeze_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenUnfreeze.CopyFrom(token_unfreeze_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.unfreezeTokenAccount,
            query_func=None
        )
