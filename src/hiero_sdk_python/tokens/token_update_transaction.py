"""
hiero_sdk_python.transaction.token_update_transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenUpdateParams, TokenUpdateKeys, and TokenUpdateTransaction for updating
token properties (settings and keys) on the Hedera network via the HTS API.
"""
from typing import Optional
from dataclasses import dataclass
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_key_validation import TokenKeyValidation
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import token_update_pb2, transaction_body_pb2
from google.protobuf.wrappers_pb2 import BytesValue, StringValue

@dataclass
class TokenUpdateParams:
    """
    Represents token attributes that can be updated.

    Attributes:
        treasury_account_id (optional): The new treasury account ID.
        token_name (optional): The new name of the token.
        token_symbol (optional): The new symbol of the token.
        token_memo (optional): The new memo for the token.
        metadata (optional): The new metadata for the token.
    """
    treasury_account_id: Optional[AccountId] = None
    token_name: Optional[str] = None
    token_symbol: Optional[str] = None
    token_memo: Optional[str] = None
    metadata: Optional[bytes] = None

@dataclass
class TokenUpdateKeys:
    """
    Represents cryptographic keys that can be updated for a token.
    Does not include treasury_key which is for transaction signing.

    Attributes:
        admin_key: The new admin key for the token.
        supply_key: The new supply key for the token.
        freeze_key: The new freeze key for the token.
        wipe_key: The new wipe key for the token.
        metadata_key: The new metadata key for the token.
        pause_key: The new pause key for the token.
    """
    admin_key: Optional[PrivateKey] = None
    supply_key: Optional[PrivateKey] = None
    freeze_key: Optional[PrivateKey] = None
    wipe_key: Optional[PrivateKey] = None
    metadata_key: Optional[PrivateKey] = None
    pause_key: Optional[PrivateKey] = None


class TokenUpdateTransaction(Transaction):
    """
    A transaction that updates an existing token's properties.

    This transaction can be used to update various properties of a token including its name,
    symbol, treasury account, keys, and other attributes. Only accounts with the proper key
    signing authority can update token properties.

    Args:
        token_id (TokenId, optional): The ID of the token to update.
        token_params (TokenUpdateParams, optional): Parameters of token properties to update.
        token_keys (TokenUpdateKeys, optional): New keys to set for the token.
        token_key_validation (TokenKeyValidation, optional): The validation mode for token keys.
            Defaults to FULL_VALIDATION.
    """
    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        token_params: Optional[TokenUpdateParams] = None,
        token_keys: Optional[TokenUpdateKeys] = None,
        token_key_verification_mode: TokenKeyValidation = TokenKeyValidation.FULL_VALIDATION
    ) -> None:
        """
        Initializes a new TokenUpdateTransaction instance with token parameters and optional keys.

        This transaction can be built in two ways to support flexibility:
        1) By passing a fully-formed TokenId, TokenUpdateParams and TokenUpdateKeys
        2) By passing `None` (or partial) then using the `set_*` methods
            Validation is deferred until build time (`build_transaction_body()`), 
            so you won't fail immediately if fields are missing at creation.

        Args:
            token_id (TokenId, optional): The ID of the token to update.
            token_params (TokenUpdateParams, optional): the token properties to update.
            token_keys (TokenUpdateKeys, optional): New keys to set for the token.
            token_key_validation (TokenKeyValidation, optional): The validation mode for token keys.
                Defaults to FULL_VALIDATION.
        """
        super().__init__()
        
        self.token_id: Optional[TokenId] = token_id
        
        # Initialize params attributes
        params: TokenUpdateParams = token_params or TokenUpdateParams()
        self.treasury_account_id: Optional[AccountId] = params.treasury_account_id
        self.token_name: Optional[str] = params.token_name
        self.token_symbol: Optional[str] = params.token_symbol
        self.token_memo: Optional[str] = params.token_memo
        self.metadata: Optional[bytes] = params.metadata

        # Initialize keys attributes
        keys: TokenUpdateKeys = token_keys or TokenUpdateKeys()
        self.admin_key: Optional[PrivateKey] = keys.admin_key
        self.freeze_key: Optional[PrivateKey] = keys.freeze_key
        self.wipe_key: Optional[PrivateKey] = keys.wipe_key
        self.supply_key: Optional[PrivateKey] = keys.supply_key
        self.pause_key: Optional[PrivateKey] = keys.pause_key
        self.metadata_key: Optional[PrivateKey] = keys.metadata_key

        self.token_key_verification_mode: TokenKeyValidation = token_key_verification_mode

        # Set default transaction fee to 2 HBAR for token update transactions
        self._default_transaction_fee: int = Hbar(2).to_tinybars()

    def set_token_id(self, token_id: TokenId) -> "TokenUpdateTransaction":
        """
        Sets the token ID to update.

        Args:
            token_id (TokenId): The ID of the token to update.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_treasury_account_id(self, treasury_account_id: AccountId) -> "TokenUpdateTransaction":
        """
        Sets the new treasury account ID for the token.

        Args:
            treasury_account_id (AccountId): The new treasury account ID.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.treasury_account_id = treasury_account_id
        return self
    
    def set_token_name(self, token_name: str) -> "TokenUpdateTransaction":
        """
        Sets the new name for the token.

        Args:
            token_name (str): The new name to set for the token.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_name = token_name
        return self
    
    def set_token_symbol(self, token_symbol: str) -> "TokenUpdateTransaction":
        """
        Sets the new symbol for the token.

        Args:
            token_symbol (str): The new symbol to set for the token.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_symbol = token_symbol
        return self
    
    def set_token_memo(self, token_memo: str) -> "TokenUpdateTransaction":
        """
        Sets the new memo for the token.

        Args:
            token_memo (str): The new memo to set for the token.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_memo = token_memo
        return self
    
    def set_metadata(self, metadata: bytes) -> "TokenUpdateTransaction":
        """
        Sets the new metadata for the token.

        Args:
            metadata (bytes): The new metadata to set for the token.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.metadata = metadata
        return self
    
    def set_admin_key(self, admin_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new admin key for the token.

        Args:
            admin_key (PrivateKey): The new admin key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self
    
    def set_freeze_key(self, freeze_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new freeze key for the token.

        Args:
            freeze_key (PrivateKey): The new freeze key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.freeze_key = freeze_key
        return self
    
    def set_wipe_key(self, wipe_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new wipe key for the token.

        Args:
            wipe_key (PrivateKey): The new wipe key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.wipe_key = wipe_key
        return self
    
    def set_supply_key(self, supply_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new supply key for the token.

        Args:
            supply_key (PrivateKey): The new supply key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.supply_key = supply_key
        return self
    
    def set_pause_key(self, pause_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new pause key for the token.

        Args:
            pause_key (PrivateKey): The new pause key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.pause_key = pause_key
        return self
    
    def set_metadata_key(self, metadata_key: PrivateKey) -> "TokenUpdateTransaction":
        """
        Sets the new metadata key for the token.

        Args:
            metadata_key (PrivateKey): The new metadata key to set.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.metadata_key = metadata_key
        return self
    
    def set_key_verification_mode(self, key_verification_mode: TokenKeyValidation) -> "TokenUpdateTransaction":
        """
        Sets the key verification mode for the token.

        Args:
            key_verification_mode (TokenKeyValidation): The validation mode to use for token keys.

        Returns:
            TokenUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_key_verification_mode = key_verification_mode
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token update.

        Returns:
            TransactionBody: The protobuf transaction body containing the token update details.

        Raises:
            ValueError: If token_id is not set.
        """
        if self.token_id is None:
            raise ValueError("Missing token ID")
        
        token_update_body = token_update_pb2.TokenUpdateTransactionBody(
            token=self.token_id._to_proto(),
            treasury=self.treasury_account_id._to_proto() if self.treasury_account_id else None,
            name=self.token_name,
            memo=StringValue(value=self.token_memo) if self.token_memo else None,
            metadata=BytesValue(value=self.metadata) if self.metadata else None,
            symbol=self.token_symbol,
            key_verification_mode=self.token_key_verification_mode._to_proto()
        )
        self._set_keys_to_proto(token_update_body)
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenUpdate.CopyFrom(token_update_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token update transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs.
        
        Returns:
            _Method: An object containing the transaction function to update tokens.
        """
        return _Method(
            transaction_func=channel.token.updateToken,
            query_func=None
        )
        
    def _set_keys_to_proto(self, token_update_body: token_update_pb2.TokenUpdateTransactionBody) -> None:
        """
        Sets the keys to the protobuf transaction body.
        """
        if self.admin_key:
            token_update_body.adminKey.CopyFrom(self.admin_key.public_key()._to_proto())
        if self.freeze_key:
            token_update_body.freezeKey.CopyFrom(self.freeze_key.public_key()._to_proto())
        if self.wipe_key:
            token_update_body.wipeKey.CopyFrom(self.wipe_key.public_key()._to_proto())
        if self.supply_key:
            token_update_body.supplyKey.CopyFrom(self.supply_key.public_key()._to_proto())
        if self.metadata_key:
            token_update_body.metadata_key.CopyFrom(self.metadata_key.public_key()._to_proto())
        if self.pause_key:
            token_update_body.pause_key.CopyFrom(self.pause_key.public_key()._to_proto())
