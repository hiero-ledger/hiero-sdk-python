"""
hiero_sdk_python.transaction.token_revoke_kyc_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenRevokeKycTransaction, a subclass of Transaction for revoking
Know-Your-Customer (KYC) status from an account for a specific token on the
Hedera network via the Hedera Token Service (HTS) API.
"""
from typing import Optional
from hiero_sdk_python.hapi.services import token_revoke_kyc_pb2, transaction_body_pb2
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId

class TokenRevokeKycTransaction(Transaction):
    """
    Represents a token revoke KYC transaction on the network.
    
    This transaction revokes KYC (Know Your Customer) status from an account for a specific token.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token revoke KYC transaction.
    """
    def __init__(self, token_id: Optional[TokenId] = None, account_id: Optional[AccountId] = None) -> None:
        """
        Initializes a new TokenRevokeKycTransaction instance with the token ID and account ID.

        Args:
            token_id (TokenId, optional): The ID of the token to revoke KYC from.
            account_id (AccountId, optional): The ID of the account to revoke KYC from.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.account_id: Optional[AccountId] = account_id
    
    def set_token_id(self, token_id: TokenId) -> "TokenRevokeKycTransaction":
        """
        Sets the token ID for this revoke KYC transaction.

        Args:
            token_id (TokenId): The ID of the token to revoke KYC from.

        Returns:
            TokenRevokeKycTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_account_id(self, account_id: AccountId) -> "TokenRevokeKycTransaction":
        """
        Sets the account ID for this revoke KYC transaction.

        Args:
            account_id (AccountId): The ID of the account to revoke KYC from.

        Returns:
            TokenRevokeKycTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self
    
    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds the transaction body for this token revoke KYC transaction.

        Returns:
            transaction_body_pb2.TransactionBody: The built transaction body.
            
        Raises:
            ValueError: If the token ID or account ID is not set.
        """
        if self.token_id is None:
            raise ValueError("Missing token ID")

        if self.account_id is None:
            raise ValueError("Missing account ID")
        
        token_revoke_kyc_body = token_revoke_kyc_pb2.TokenRevokeKycTransactionBody(
            token=self.token_id._to_proto(),
            account=self.account_id._to_proto()
        )
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenRevokeKyc.CopyFrom(token_revoke_kyc_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token revoke KYC transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs
        
        Returns:
            _Method: An object containing the transaction function to revoke KYC.
        """
        return _Method(
            transaction_func=channel.token.revokeKycFromTokenAccount,
            query_func=None
        )

    def _from_proto(self, proto: token_revoke_kyc_pb2.TokenRevokeKycTransactionBody) -> "TokenRevokeKycTransaction":
        """
        Initializes a new TokenRevokeKycTransaction instance from a protobuf object.

        Args:
            proto (TokenRevokeKycTransactionBody): The protobuf object to initialize from.

        Returns:
            TokenRevokeKycTransaction: This transaction instance.
        """
        self.token_id = TokenId._from_proto(proto.token)
        self.account_id = AccountId._from_proto(proto.account)
        return self
