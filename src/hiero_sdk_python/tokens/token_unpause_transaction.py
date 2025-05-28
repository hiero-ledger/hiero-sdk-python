from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services.token_unpause_pb2 import TokenUnpauseTransactionBody
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenUnpauseTransaction(Transaction):
    """
    Represents a token unpause transaction. 
    
    A token unpause transaction resumes a previously paused token, allowing it to be involved in operations again.
    The token is required to have a pause key and the pause key must sign.
    Once a token is unpaused, token status will update from paused to unpaused.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token unpause transaction.
    """
    def __init__(self, token_id=None):
        """
        Initializes a new TokenUnpauseTransaction instance with optional token_id.
        Args:
            token_id (TokenId, optional): The ID of the token to be unpaused.
        """
        super().__init__()
        self.token_id : TokenId = token_id

    def set_token_id(self, token_id):
        """
        Sets the ID of the token to be unpaused.
        Args:
            token_id (TokenId): The ID of the token to be unpaused.
        Returns:
            TokenUnpauseTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token unpause.
        Returns:
            TransactionBody: The protobuf transaction body containing the token unpause details.
        
        Raises:
        ValueError: If no token_id has been set.
        """
        if self.token_id is None:
            raise ValueError("token_id must be set before building the transaction body")

        token_unpause_body = TokenUnpauseTransactionBody(
            token=self.token_id.to_proto()
        )
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenUnpause.CopyFrom(token_unpause_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.unpauseToken,
            query_func=None
        )

    def _from_proto(self, proto: TokenUnpauseTransactionBody):
        """
        Deserializes a TokenUnpauseTransactionBody from a protobuf object.
        Args:
            proto (TokenUnpauseTransactionBody): The protobuf object to deserialize.
        Returns:
            TokenUnpauseTransaction: Returns self for method chaining.
        """
        self.token_id = TokenId.from_proto(proto.token)
        return self
        