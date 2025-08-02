"""
hiero_sdk_python.transaction.token_grant_kyc_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenGrantKycTransaction, a subclass of Transaction for granting KYC status
to accounts for specific tokens on the Hedera network via the Hedera Token Service (HTS) API.
"""
from typing import Optional
from hiero_sdk_python.hapi.services import token_grant_kyc_pb2, transaction_body_pb2
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId

class TokenGrantKycTransaction(Transaction):
    """
    Represents a token grant KYC transaction on the network.
    
    This transaction grants KYC (Know Your Customer) status to an account for a specific token.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token grant KYC transaction.
    """
    def __init__(
        self, 
        token_id: Optional[TokenId] = None, 
        account_id: Optional[AccountId] = None
    ) -> None:
        """
        Initializes a new TokenGrantKycTransaction instance with the token ID and account ID.

        Args:
            token_id (TokenId, optional): The ID of the token to grant KYC to.
            account_id (AccountId, optional): The ID of the account to grant KYC to.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.account_id: Optional[AccountId] = account_id
    
    def set_token_id(self, token_id: TokenId) -> "TokenGrantKycTransaction":
        """
        Sets the token ID for this grant KYC transaction.

        Args:
            token_id (TokenId): The ID of the token to grant KYC to.

        Returns:
            TokenGrantKycTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_account_id(self, account_id: AccountId) -> "TokenGrantKycTransaction":
        """
        Sets the account ID for this grant KYC transaction.

        Args:
            account_id (AccountId): The ID of the account to grant KYC to.

        Returns:
            TokenGrantKycTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self
    
    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds the transaction body for this token grant KYC transaction.

        Returns:
            TransactionBody: The built transaction body.
            
        Raises:
            ValueError: If the token ID or account ID is not set.
        """
        if self.token_id is None:
            raise ValueError("Missing token ID")

        if self.account_id is None:
            raise ValueError("Missing account ID")
        
        token_grant_kyc_body = token_grant_kyc_pb2.TokenGrantKycTransactionBody(
            token=self.token_id._to_proto(),
            account=self.account_id._to_proto()
        )
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenGrantKyc.CopyFrom(token_grant_kyc_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token grant KYC transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to grant KYC.
        """
        return _Method(
            transaction_func=channel.token.grantKycToTokenAccount,
            query_func=None
        )

    def _from_proto(self, proto: token_grant_kyc_pb2.TokenGrantKycTransactionBody) -> "TokenGrantKycTransaction":
        """
        Initializes a new TokenGrantKycTransaction instance from a protobuf object.

        Args:
            proto (token_grant_kyc_pb2.TokenGrantKycTransactionBody): The protobuf object to initialize from.

        Returns:
            TokenGrantKycTransaction: This transaction instance.
        """
        self.token_id = TokenId._from_proto(proto.token)
        self.account_id = AccountId._from_proto(proto.account)
        return self
