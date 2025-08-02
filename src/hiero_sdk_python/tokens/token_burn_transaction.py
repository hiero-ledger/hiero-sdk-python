"""
hiero_sdk_python.transaction.token_burn_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenBurnTransaction, a subclass of Transaction for burning fungible and
non-fungible tokens on the Hedera network using the Hedera Token Service (HTS) API.
"""
from typing import List, Optional

from hiero_sdk_python.hapi.services.token_burn_pb2 import TokenBurnTransactionBody
from hiero_sdk_python.hapi.services import transaction_body_pb2
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId

class TokenBurnTransaction(Transaction):
    """
    Represents a token burn transaction on the network.
    
    This transaction burns tokens, effectively removing them from circulation.
    Can burn fungible tokens by amount or non-fungible tokens by serial numbers.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token burn transaction.
    """
    def __init__(
        self, 
        token_id: Optional[TokenId] = None, 
        amount: Optional[int] = None, 
        serials: Optional[List[int]] = None
    ) -> None:
        """
        Initializes a new TokenBurnTransaction instance with optional token_id, amount, and serials.

        Args:
            token_id (TokenId, optional): The ID of the token to burn.
            amount (int, optional): The amount of fungible tokens to burn.
            serials (list[int], optional): The serial numbers of non-fungible tokens to burn.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.amount: Optional[int] = amount
        self.serials: Optional[List[int]] = serials if serials else []
    
    def set_token_id(self, token_id: TokenId) -> "TokenBurnTransaction":
        """
        Sets the token ID for this burn transaction.

        Args:
            token_id (TokenId): The ID of the token to burn.

        Returns:
            TokenBurnTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_amount(self, amount: int) -> "TokenBurnTransaction":
        """
        Sets the amount of fungible tokens to burn.

        Args:
            amount (int): The number of tokens to burn.

        Returns:
            TokenBurnTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.amount = amount
        return self
    
    def set_serials(self, serials: List[int]) -> "TokenBurnTransaction":
        """
        Sets the list of serial numbers of non-fungible tokens to burn.

        Args:
            serials (list[int]): List of serial numbers to burn.

        Returns:
            TokenBurnTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.serials = serials
        return self
        
    def add_serial(self, serial: int) -> "TokenBurnTransaction":
        """
        Adds a single serial number to the list of non-fungible tokens to burn.

        Args:
            serial (int): The serial number to add.

        Returns:
            TokenBurnTransaction: This transaction instance.

        """
        self._require_not_frozen()
        self.serials.append(serial)
        return self
        
    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds the transaction body for this token burn transaction.

        Returns:
            TransactionBody: The built transaction body.
        
        Raises:
            ValueError: If the token ID is not set or if both amount and serials are provided.
        """
        if self.token_id is None:
            raise ValueError("Missing token ID")

        if self.amount and self.serials:
            raise ValueError("Cannot burn both amount and serial in the same transaction")

        token_burn_body = TokenBurnTransactionBody(
            token=self.token_id._to_proto(),
            amount=self.amount,
            serialNumbers=self.serials
        )
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenBurn.CopyFrom(token_burn_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token burn transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to burn tokens.
        """
        return _Method(
            transaction_func=channel.token.burnToken,
            query_func=None
        )
    
    def _from_proto(self, proto: TokenBurnTransactionBody) -> "TokenBurnTransaction":
        """
        Deserializes a TokenBurnTransactionBody from a protobuf object.

        Args:
            proto (TokenBurnTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenBurnTransaction: Returns self for method chaining.
        """
        self.token_id = TokenId._from_proto(proto.token)
        self.amount = proto.amount
        self.serials = proto.serialNumbers
        return self
