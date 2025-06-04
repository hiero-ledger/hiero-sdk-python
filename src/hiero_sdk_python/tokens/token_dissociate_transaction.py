from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_dissociate_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenDissociateTransaction(Transaction):
    """
    Represents a token dissociate transaction on the Hedera network.

    This transaction dissociates the specified tokens with an account,
    meaning the account can no longer hold or transact with those tokens.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token dissociate transaction.
    """

    def __init__(self, account_id=None, token_ids=None):
        """
        Initializes a new TokenDissociateTransaction instance with default values.
        """
        super().__init__()
        self.account_id = account_id
        self.token_ids = token_ids or []

        self._default_transaction_fee = 500_000_000

    def set_account_id(self, account_id):
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def add_token_id(self, token_id):
        self._require_not_frozen()
        self.token_ids.append(token_id)
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token dissociation.

        Returns:
            TransactionBody: The protobuf transaction body containing the token dissociation details.

        Raises:
            ValueError: If account ID or token IDs are not set.
        """
        if not self.account_id or not self.token_ids:
            raise ValueError("Account ID and token IDs must be set.")

        token_dissociate_body = token_dissociate_pb2.TokenDissociateTransactionBody(
            account=self.account_id._to_proto(),
            tokens=[token_id._to_proto() for token_id in self.token_ids]
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenDissociate.CopyFrom(token_dissociate_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.dissociateTokens,
            query_func=None
        )