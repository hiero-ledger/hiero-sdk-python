"""
hiero_sdk_python.transaction.token_pause_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenPauseTransaction, a subclass of Transaction for pausing a specified token
on the Hedera network via the Hedera Token Service (HTS) API.
"""
from typing import Optional
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_pause_pb2, transaction_body_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenPauseTransaction(Transaction):
    """
    Represents a token pause transaction. 
    
    A token pause transaction prevents a token from being involved in any operation.

    The token is required to have a pause key and the pause key must sign.
    Once a token is paused, token status will update from unpaused to paused. 
    Those without a pause key will state PauseNotApplicable.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token pause transaction.
    """
    def __init__(self, token_id: Optional[TokenId] = None) -> None:
        """
        Initializes a new TokenPauseTransaction instance with optional token_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be paused.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        
    def set_token_id(self, token_id: TokenId) -> "TokenPauseTransaction":
        """
        Sets the ID of the token to be paused.

        Args:
            token_id (TokenId): The ID of the token to be paused.

        Returns:
            TokenPauseTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token pause.

        Returns:
            TransactionBody: The protobuf transaction body containing the token pause details.
        
        Raises:
        ValueError: If no token_id has been set.
        """
        if self.token_id is None or self.token_id.num == 0:
            raise ValueError("token_id must be set before building the transaction body")

        token_pause_body = token_pause_pb2.TokenPauseTransactionBody(
            token=self.token_id._to_proto()
        )
        transaction_body:transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.token_pause.CopyFrom(token_pause_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.pauseToken,
            query_func=None
        )
    
    def _from_proto(self, proto: token_pause_pb2.TokenPauseTransactionBody) -> "TokenPauseTransaction":
        """
        Deserializes a TokenPauseTransactionBody from a protobuf object.

        Args:
            proto (TokenPauseTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenPauseTransaction: Returns self for method chaining.
        """
        self.token_id = TokenId._from_proto(proto.token)
        return self
