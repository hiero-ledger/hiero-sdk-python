from hedera_sdk_python.transaction.transaction import Transaction
from hedera_sdk_python.hapi.services import token_associate_pb2
from hedera_sdk_python.response_code import ResponseCode
from hedera_sdk_python.tokens.token_id import TokenId

class TokenAssociateTransaction(Transaction):
    """
    Represents a token associate transaction on the Hedera network.
    """

    def __init__(self, account_id=None, token_ids=None):
        """
        Initializes a new TokenAssociateTransaction instance.

        Args:
            account_id (AccountId, optional): The account to associate tokens with.
            token_ids (list or single TokenId/str, optional): Tokens to associate with the account.
        """
        super().__init__()
        self.account_id = account_id
        self.token_ids = self._normalize_token_ids(token_ids)

        self._default_transaction_fee = 500_000_000

    def set_account_id(self, account_id):
        """
        Sets the account ID for the transaction.

        Args:
            account_id (AccountId): The account to associate tokens with.

        Returns:
            TokenAssociateTransaction: Self for method chaining.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_token_ids(self, token_ids):
        """
        Sets multiple tokens for the transaction.

        Args:
            token_ids (list or single TokenId/str): Tokens to associate.

        Returns:
            TokenAssociateTransaction: Self for method chaining.
        """
        self._require_not_frozen()
        self.token_ids = self._normalize_token_ids(token_ids)
        return self

    def add_token_id(self, token_id):
        """
        Adds a single token to the transaction.

        Args:
            token_id (TokenId or str): Token to associate.

        Returns:
            TokenAssociateTransaction: Self for method chaining.
        """
        self._require_not_frozen()
        self.token_ids.append(TokenId.from_string(token_id) if isinstance(token_id, str) else token_id)
        return self

    @staticmethod
    def _normalize_token_ids(token_ids):
        """
        Converts a single token or list of tokens to a list of TokenId objects.

        Args:
            token_ids (list, TokenId, or str): Tokens to normalize.

        Returns:
            list: A list of TokenId objects.
        """
        if not token_ids:
            return []
        if isinstance(token_ids, (TokenId, str)):
            return [TokenId.from_string(token_ids) if isinstance(token_ids, str) else token_ids]
        return [TokenId.from_string(t) if isinstance(t, str) else t for t in token_ids]

    def build_transaction_body(self):
        """
        Builds the transaction body.
        """
        if not self.account_id or not self.token_ids:
            raise ValueError("Account ID and token IDs must be set.")

        token_associate_body = token_associate_pb2.TokenAssociateTransactionBody(
            account=self.account_id.to_proto(),
            tokens=[token_id.to_proto() for token_id in self.token_ids]
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenAssociate.CopyFrom(token_associate_body)
        return transaction_body

    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the token association transaction using the provided client.

        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.

        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.

        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """
        response = client.token_stub.associateTokens(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")

        receipt = self.get_receipt(client)
        return receipt

    def get_receipt(self, client, timeout=60):
        """
        Retrieves the receipt for the transaction.

        Args:
            client (Client): The client instance.
            timeout (int): Maximum time in seconds to wait for the receipt.

        Returns:
            TransactionReceipt: The transaction receipt from the network.

        Raises:
            Exception: If the transaction ID is not set or if receipt retrieval fails.
        """
        if self.transaction_id is None:
            raise Exception("Transaction ID is not set.")

        receipt = client.get_transaction_receipt(self.transaction_id, timeout)
        return receipt
