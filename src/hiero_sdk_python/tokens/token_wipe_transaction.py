"""
hiero_sdk_python.transaction.token_wipe_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenWipeTransaction, a subclass of Transaction for wiping fungible tokens and NFTs
from accounts on the Hedera network via the Hedera Token Service (HTS) API.
"""
from typing import Optional, List
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_wipe_account_pb2, transaction_body_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenWipeTransaction(Transaction):
    """
    Represents a token wipe transaction on the Hedera network.
    
    This transaction wipes (removes) tokens from an account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token wipe transaction.
    """
    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        account_id: Optional[AccountId] = None,
        amount: Optional[int] = None,
        serial: Optional[List[int]] = None
    ) -> None:
        """
        Initializes a new TokenWipeTransaction instance with optional token_id and account_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be wiped.
            account_id (AccountId, optional): The ID of the account to have their tokens wiped.
            amount (int, optional): The amount of tokens to wipe.
            serial (list[int], optional): The serial numbers of NFTs to wipe.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.account_id: Optional[AccountId] = account_id
        self.amount: Optional[int] = amount
        self.serial: List[int] = serial if serial else []

    def set_token_id(self, token_id: TokenId) -> "TokenWipeTransaction":
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

    def set_account_id(self, account_id: AccountId) -> "TokenWipeTransaction":
        """
        Sets the ID of the account to have their tokens wiped.

        Args:
            account_id (AccountId): The ID of the account to have their tokens wiped.
        
        Returns:
            TokenWipeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_amount(self, amount: int) -> "TokenWipeTransaction":
        """
        Sets the amount of tokens to wipe.

        Args:
            amount (int): The amount of tokens to wipe.
        
        Returns:
            TokenWipeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.amount = amount
        return self

    def set_serial(self, serial: List[int]) -> "TokenWipeTransaction":
        """
        Sets the serial numbers of NFTs to wipe.

        Args:
            serial (List[int]): The serial numbers of the NFTs to wipe.
        
        Returns:
            TokenWipeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.serial = serial
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token wipe.

        Returns:
            TransactionBody: The protobuf transaction body containing the token wipe details.
        """
        token_wipe_body = token_wipe_account_pb2.TokenWipeAccountTransactionBody(
            token=self.token_id and self.token_id._to_proto(),
            account=self.account_id and self.account_id._to_proto(),
            amount=self.amount,
            serialNumbers=self.serial
        )
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenWipe.CopyFrom(token_wipe_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.wipeTokenAccount,
            query_func=None
        )
    
    def _from_proto(self, proto: token_wipe_account_pb2.TokenWipeAccountTransactionBody) -> "TokenWipeTransaction":
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
