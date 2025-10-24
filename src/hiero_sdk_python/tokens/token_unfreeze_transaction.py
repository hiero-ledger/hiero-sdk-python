"""
hiero_sdk_python.tokens.token_unfreeze_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenUnfreezeTransaction, a subclass of Transaction for un-freezing a specified token
for an account on the Hedera network using the Hedera Token Service (HTS) API.
"""
from typing import Optional
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_unfreeze_account_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId

class TokenUnfreezeTransaction(Transaction):
    """
    Represents a token unfreeze transaction on the Hedera network.
    
    This transaction unfreezes specified tokens for a given account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token unfreeze transaction.
    """

    def __init__(
        self,
        account_id: Optional[AccountId] = None,
        token_id: Optional[TokenId] = None
    ) -> None:
        """
        Initializes a new TokenUnfreezeTransaction instance with default values.
        Args:
            account_id (AccountId, optional): The ID of the account to unfreeze tokens for.
            token_id (TokenId, optional): The ID of the token to unfreeze.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.account_id: Optional[AccountId] = account_id
        self._default_transaction_fee: int = 3_000_000_000

    def set_token_id(self, token_id: TokenId) -> "TokenUnfreezeTransaction":
        """
        Sets the token ID for this unfreeze transaction.
        Args:
            token_id (TokenId): The ID of the token to unfreeze.
        Returns:
            TokenUnfreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_account_id(self, account_id: AccountId) -> "TokenUnfreezeTransaction":
        """
        Sets the account ID for this unfreeze transaction.
        Args:
            account_id (AccountId): The ID of the account to unfreeze tokens for.
        Returns:
            TokenUnfreezeTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self


    def _build_proto_body(self) -> token_unfreeze_account_pb2.TokenUnfreezeAccountTransactionBody:
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
        
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token unfreeze.

        Returns:
            TransactionBody: The protobuf transaction body containing the token unfreeze details.
        """
        token_unfreeze_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
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
