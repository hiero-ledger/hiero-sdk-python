"""
hiero_sdk_python.tokens.token_unpause_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides the TokenUnpauseTransaction class a subclass of Transaction that
facilitates unpausing a specified token on the Hedera network using the
Hedera Token Service (HTS) API.
"""
from typing import Optional
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody
)
from hiero_sdk_python.hapi.services.token_unpause_pb2 import TokenUnpauseTransactionBody
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction

class TokenUnpauseTransaction(Transaction):
    """
    Represents a token unpause transaction on the Hedera network.
    
    This transaction unpauses specified tokens.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token unpause transaction.
    """

    def __init__(self, token_id: Optional[TokenId] = None) -> None:
        """
        Initializes a new TokenUnpauseTransaction instance with default values.

        Args:
            token_id (Optional[TokenId]): The ID of the token to unpause.
        """
        super().__init__()
        self.token_id:  Optional[TokenId] = None

        if token_id is not None:
            self.set_token_id(token_id)

    def set_token_id(self, token_id: TokenId) -> "TokenUnpauseTransaction":
        """
        Sets the token ID for this unpause transaction.

        Args:
            token_id (TokenId): The ID of the token to unpause.
            
        Returns:
            TokenUnpauseTransaction: This current instance of transaction.
        """
        self._require_not_frozen()

        #Check if the tokenId is instance of TokenId
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be an instance of TokenId")

        self.token_id = token_id
        return self

    def _validate_checksum(self, client: "Client") -> None:
        """
        Validates the checksum for the token ID associated with this transaction.

        Args:
            client (Client): The client instance used for validation.
        """
        if self.token_id is not None:
            self.token_id.validate_checksum(client)

    @classmethod
    def _from_proto(cls, proto: TokenUnpauseTransactionBody) -> "TokenUnpauseTransaction":
        """
        Construct TokenUnpauseTransaction from TokenUnpauseTransactionBody.

        Args:
            proto (TokenUnpauseTransactionBody): The protobuf body of TokenUnpauseTransaction
        
        Returns:
            TokenUnpauseTransaction: A new instance of TokenUnpauseTransaction
        """
        token_id = TokenId._from_proto(proto.token) if proto.token else None
        return cls(token_id=token_id)

    def _build_proto_body(self) -> TokenUnpauseTransactionBody:
        """
        Returns the protobuf body for the token unpause transaction.
        
        Returns:
            TokenUnpauseTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If account ID or token ID is not set.
        """
        if self.token_id is None:
            raise ValueError("Missing token ID")

        return TokenUnpauseTransactionBody(
            token=self.token_id._to_proto()
        )

    def build_transaction_body(self) -> TransactionBody:
        """
        Builds and returns the protobuf transaction body for token unpause.

        Returns:
            TransactionBody: The protobuf transaction body containing the token unpause details.
        """
        token_unpause_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.token_unpause.CopyFrom(token_unpause_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token unpause transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_unpause_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.token_unpause.CopyFrom(token_unpause_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.unpauseToken,
            query_func=None
        )
