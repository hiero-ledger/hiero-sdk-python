from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services.token_wipe_account_pb2 import TokenWipeAccountTransactionBody
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenWipeTransaction(Transaction):
    """
    Represents a token wipe transaction on the Hedera network.
    
    This transaction wipes (removes) tokens from an account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token wipe transaction.
    """
    def __init__(self, token_id=None, account_id=None, amount=None, serial=[]):
        """
        Initializes a new TokenWipeTransaction instance with optional token_id and account_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be wiped.
            account_id (AccountId, optional): The ID of the account to have their tokens wiped.
            amount (int, optional): The amount of tokens to wipe.
            serial (list[int], optional): The serial numbers of NFTs to wipe.
        """
        super().__init__()
        self.token_id : TokenId = token_id
        self.account_id : AccountId = account_id
        self.amount : int = amount
        self.serial : list[int] = serial
        
    def set_token_id(self, token_id):
        """
        Sets the ID of the token to be wiped.

        Args:
            token_id (TokenId): The ID of the token to be wiped.

        Returns:
            TokenWipeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_account_id(self, account_id):
        self._require_not_frozen()
        self.account_id = account_id
        return self
    
    def set_amount(self, amount):
        self._require_not_frozen()
        self.amount = amount
        return self
    
    def set_serial(self, serial):
        self._require_not_frozen()
        self.serial = serial
        return self
    
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token wipe.

        Returns:
            TransactionBody: The protobuf transaction body containing the token wipe details.
        """
        token_wipe_body = TokenWipeAccountTransactionBody(
            token=self.token_id and self.token_id._to_proto(),
            account=self.account_id and self.account_id._to_proto(),
            amount=self.amount,
            serialNumbers=self.serial
        )
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenWipe.CopyFrom(token_wipe_body)
        return transaction_body
    
    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.wipeTokenAccount,
            query_func=None
        )
    
    def _from_proto(self, proto: TokenWipeAccountTransactionBody):
        """
        Deserializes a TokenWipeAccountTransactionBody from a protobuf object.

        Args:
            proto (TokenWipeAccountTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenWipeTransaction: Returns self for method chaining.
        """
        self.token_id = TokenId._from_proto(proto.token)
        self.account_id = AccountId._from_proto(proto.account)
        self.amount = proto.amount
        self.serial = proto.serialNumbers
        return self