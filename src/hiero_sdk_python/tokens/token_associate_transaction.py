from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import token_associate_pb2
from hiero_sdk_python.transaction.transaction import Transaction


class TokenAssociateTransaction(Transaction):
    """
    Represents a token associate transaction on the Hedera network.

    This transaction associates the specified tokens with an account,
    allowing the account to hold and transact with those tokens.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token association transaction.
    """

    def __init__(self, account_id=None, token_ids=None):
        """
        Initializes a new TokenAssociateTransaction instance with optional keyword arguments.

        Args:
            account_id (AccountId, optional): The account to associate tokens with.
            token_ids (list of TokenId, optional): The tokens to associate with the account.
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
        Builds and returns the protobuf transaction body for token association.

        Returns:
            TransactionBody: The protobuf transaction body containing the token association details.

        Raises:
            ValueError: If account ID or token IDs are not set.
        """
        if not self.account_id or not self.token_ids:
            raise ValueError("Account ID and token IDs must be set.")

        token_associate_body = token_associate_pb2.TokenAssociateTransactionBody(
            account=self.account_id._to_proto(),
            tokens=[token_id._to_proto() for token_id in self.token_ids]
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenAssociate.CopyFrom(token_associate_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.associateTokens,
            query_func=None
        )