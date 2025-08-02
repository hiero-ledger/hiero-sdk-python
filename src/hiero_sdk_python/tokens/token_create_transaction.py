"""
Module for creating and validating Hedera token transactions.

This module includes:
- TokenCreateValidator: Validates token creation parameters.
- TokenParams: Represents token attributes.
- TokenKeys: Represents cryptographic keys for tokens.
- TokenCreateTransaction: Handles token creation transactions on Hedera.
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_create_pb2, basic_types_pb2, transaction_body_pb2
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

DEFAULT_TRANSACTION_FEE = 3_000_000_000

class TokenCreateValidator:
    """Token, key and freeze checks for creating a token as per the proto"""

    @staticmethod
    def _validate_token_params(token_params):
        """
        Ensure valid values for the token characteristics.
        """
        TokenCreateValidator._validate_required_fields(token_params)
        TokenCreateValidator._validate_name_and_symbol(token_params)
        TokenCreateValidator._validate_initial_supply(token_params)
        TokenCreateValidator._validate_decimals_and_token_type(token_params)
        TokenCreateValidator._validate_supply_max_and_type(token_params)

    @staticmethod
    def _validate_required_fields(token_params):
        """
        Ensure all required fields are present and not empty.
        """
        required_fields = {
            "Token name": token_params.token_name,
            "Token symbol": token_params.token_symbol,
            "Treasury account ID": token_params.treasury_account_id,
        }
        for field, value in required_fields.items():
            if not value:
                raise ValueError(f"{field} is required")

    @staticmethod
    def _validate_name_and_symbol(token_params):
        """
        Ensure the token name & symbol are valid in length and do not contain a NUL character.
        """
        if len(token_params.token_name.encode()) > 100:
            raise ValueError("Token name must be between 1 and 100 bytes")
        if len(token_params.token_symbol.encode()) > 100:
            raise ValueError("Token symbol must be between 1 and 100 bytes")

        # Ensure the token name and symbol do not contain a NUL character
        for attr in ["token_name", "token_symbol"]:
            if "\x00" in getattr(token_params, attr):
                raise ValueError(
                    f"{attr.replace('_', ' ').capitalize()} must not contain the Unicode NUL character"
                )

    @staticmethod
    def _validate_initial_supply(token_params):
        """
        Ensure initial supply is a non-negative integer and does not exceed max supply.
        """
        MAXIMUM_SUPPLY = 9_223_372_036_854_775_807  # 2^63 - 1

        if (
            not isinstance(token_params.initial_supply, int)
            or token_params.initial_supply < 0
        ):
            raise ValueError("Initial supply must be a non-negative integer")
        if token_params.initial_supply > MAXIMUM_SUPPLY:
            raise ValueError(f"Initial supply cannot exceed {MAXIMUM_SUPPLY}")
        if token_params.max_supply > MAXIMUM_SUPPLY:
            raise ValueError(f"Max supply cannot exceed {MAXIMUM_SUPPLY}")


    @staticmethod
    def _validate_decimals_and_token_type(token_params):
        """
        Ensure decimals and token_type align with either fungible or non-fungible constraints.
        """
        if not isinstance(token_params.decimals, int) or token_params.decimals < 0:
            raise ValueError("Decimals must be a non-negative integer")

        if token_params.token_type == TokenType.FUNGIBLE_COMMON:
            # Fungible tokens must have an initial supply > 0
            if token_params.initial_supply <= 0:
                raise ValueError("A Fungible Token requires an initial supply greater than zero")

        elif token_params.token_type == TokenType.NON_FUNGIBLE_UNIQUE:
            # Non-fungible tokens must have zero decimals and zero initial supply
            if token_params.decimals != 0:
                raise ValueError("A Non-fungible Unique Token must have zero decimals")
            if token_params.initial_supply != 0:
                raise ValueError("A Non-fungible Unique Token requires an initial supply of zero")

    @staticmethod
    def _validate_token_freeze_status(keys, token_params):
        """Ensure account is not frozen for this token."""
        if token_params.freeze_default:
            if not keys.freeze_key:
                # Without a freeze key but a frozen account, it is immutable.
                raise ValueError("Token is permanently frozen. Unable to proceed.")

    @staticmethod
    def _validate_supply_max_and_type(token_params):
        """Ensure max supply and supply type constraints."""
        # An infinite token must have max supply = 0.
        # A finite token must have max supply > 0.
        if token_params.max_supply != 0: # Setting a max supply is only approprite for a finite token.
            if token_params.supply_type != SupplyType.FINITE: 
                raise ValueError("Setting a max supply field requires setting a finite supply type")

        # Finite tokens have the option to set a max supply >0.
        # A finite token must have max supply > 0.
        if token_params.supply_type == SupplyType.FINITE:
            if token_params.max_supply <= 0:
                raise ValueError("A finite supply token requires max_supply greater than zero 0")

            # Ensure max supply is greater than initial supply
            if token_params.initial_supply > token_params.max_supply:
                raise ValueError(
                    "Initial supply cannot exceed the defined max supply for a finite token"
                )

@dataclass
class TokenParams:
    """
    Represents token attributes such as name, symbol, decimals, and type.

    Attributes:
        token_name (required): The name of the token.
        token_symbol (required): The symbol of the token.
        treasury_account_id (required): The treasury account ID.
        decimals (optional): The number of decimals for the token. This must be zero for NFTs.
        initial_supply (optional): The initial supply of the token.
        token_type (optional): The type of the token, defaulting to fungible.
        max_supply (optional): The max tokens or NFT serial numbers.
        supply_type (optional): The token supply status as finite or infinite.
        freeze_default (optional): An initial Freeze status for accounts associated to this token.
    """

    token_name: str
    token_symbol: str
    treasury_account_id: AccountId
    decimals: int = 0  # Default to zero decimals
    initial_supply: int = 0  # Default to zero initial supply
    token_type: TokenType = TokenType.FUNGIBLE_COMMON  # Default to Fungible Common
    max_supply: int = 0 # Since defaulting to infinite
    supply_type: SupplyType = SupplyType.INFINITE # Default to infinite
    freeze_default: bool = False


@dataclass
class TokenKeys:
    """
    Represents cryptographic keys associated with a token. 
    Does not include treasury_key which is for transaction signing.

    Attributes:
        admin_key: The admin key for the token to update and delete.
        supply_key: The supply key for the token to mint and burn.
        freeze_key: The freeze key for the token to freeze and unfreeze.
        wipe_key: The wipe key for the token to wipe tokens from an account.
        pause_key: The pause key for the token to be paused.
        metadata_key: The metadata key for the token to update NFT metadata.
        kyc_key: The KYC key for the token to grant KYC to an account.
    """

    admin_key: Optional[PrivateKey] = None
    supply_key: Optional[PrivateKey] = None
    freeze_key: Optional[PrivateKey] = None
    wipe_key: Optional[PrivateKey] = None
    metadata_key: Optional[PrivateKey] = None
    pause_key: Optional[PrivateKey] = None
    kyc_key: Optional[PrivateKey] = None

class TokenCreateValidator:
    """Token, key and freeze checks for creating a token as per the proto"""

    @staticmethod
    def _validate_token_params(token_params: TokenParams) -> None:
        """
        Ensure valid values for the token characteristics.
        """
        TokenCreateValidator._validate_required_fields(token_params)
        TokenCreateValidator._validate_name_and_symbol(token_params)
        TokenCreateValidator._validate_initial_supply(token_params)
        TokenCreateValidator._validate_decimals_and_token_type(token_params)
        TokenCreateValidator._validate_supply_max_and_type(token_params)

    @staticmethod
    def _validate_required_fields(token_params: TokenParams) -> None:
        """
        Ensure all required fields are present and not empty.
        """
        required_fields = {
            "Token name": token_params.token_name,
            "Token symbol": token_params.token_symbol,
            "Treasury account ID": token_params.treasury_account_id,
        }
        for field, value in required_fields.items():
            if not value:
                raise ValueError(f"{field} is required")

    @staticmethod
    def _validate_name_and_symbol(token_params: TokenParams) -> None:
        """
        Ensure the token name & symbol are valid in length and do not contain a NUL character.
        """
        if len(token_params.token_name.encode()) > 100:
            raise ValueError("Token name must be between 1 and 100 bytes")
        if len(token_params.token_symbol.encode()) > 100:
            raise ValueError("Token symbol must be between 1 and 100 bytes")

        # Ensure the token name and symbol do not contain a NUL character
        for attr in ["token_name", "token_symbol"]:
            if "\x00" in getattr(token_params, attr):
                raise ValueError(
                    f"{attr.replace('_', ' ').capitalize()} must not contain the Unicode NUL character"
                )

    @staticmethod
    def _validate_initial_supply(token_params: TokenParams) -> None:
        """
        Ensure initial supply is a non-negative integer and does not exceed max supply.
        """
        MAXIMUM_SUPPLY = 9_223_372_036_854_775_807  # 2^63 - 1

        if (
            not isinstance(token_params.initial_supply, int)
            or token_params.initial_supply < 0
        ):
            raise ValueError("Initial supply must be a non-negative integer")
        if token_params.initial_supply > MAXIMUM_SUPPLY:
            raise ValueError(f"Initial supply cannot exceed {MAXIMUM_SUPPLY}")
        if token_params.max_supply > MAXIMUM_SUPPLY:
            raise ValueError(f"Max supply cannot exceed {MAXIMUM_SUPPLY}")


    @staticmethod
    def _validate_decimals_and_token_type(token_params: TokenParams) -> None:
        """
        Ensure decimals and token_type align with either fungible or non-fungible constraints.
        """
        if not isinstance(token_params.decimals, int) or token_params.decimals < 0:
            raise ValueError("Decimals must be a non-negative integer")

        if token_params.token_type == TokenType.FUNGIBLE_COMMON:
            # Fungible tokens must have an initial supply > 0
            if token_params.initial_supply <= 0:
                raise ValueError("A Fungible Token requires an initial supply greater than zero")

        elif token_params.token_type == TokenType.NON_FUNGIBLE_UNIQUE:
            # Non-fungible tokens must have zero decimals and zero initial supply
            if token_params.decimals != 0:
                raise ValueError("A Non-fungible Unique Token must have zero decimals")
            if token_params.initial_supply != 0:
                raise ValueError("A Non-fungible Unique Token requires an initial supply of zero")

    @staticmethod
    def _validate_token_freeze_status(keys: TokenKeys, token_params: TokenParams) -> None:
        """Ensure account is not frozen for this token."""
        if token_params.freeze_default:
            if not keys.freeze_key:
                # Without a freeze key but a frozen account, it is immutable.
                raise ValueError("Token is permanently frozen. Unable to proceed.")
            # With a freeze key but a frozen account, first unfreezing is required.
            raise ValueError(
                "Token frozen. Please complete a Token Unfreeze Transaction."
            )

    @staticmethod
    def _validate_supply_max_and_type(token_params: TokenParams) -> None:
        """Ensure max supply and supply type constraints."""
        # An infinite token must have max supply = 0.
        # A finite token must have max supply > 0.
        if token_params.max_supply != 0: # Setting a max supply is only approprite for a finite token.
            if token_params.supply_type != SupplyType.FINITE: 
                raise ValueError("Setting a max supply field requires setting a finite supply type")

        # Finite tokens have the option to set a max supply >0.
        # A finite token must have max supply > 0.
        if token_params.supply_type == SupplyType.FINITE:
            if token_params.max_supply <= 0:
                raise ValueError("A finite supply token requires max_supply greater than zero 0")

            # Ensure max supply is greater than initial supply
            if token_params.initial_supply > token_params.max_supply:
                raise ValueError(
                    "Initial supply cannot exceed the defined max supply for a finite token"
                )

class TokenCreateTransaction(Transaction):
    """
    Represents a token creation transaction on the Hedera network.

    This transaction creates a new token with specified properties, such as
    name and symbol, leveraging the token and key params.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token creation transaction.
    """

    def __init__(self, token_params: Optional[TokenParams] = None, keys: Optional[TokenKeys] = None) -> None:
        """
        Initializes a new TokenCreateTransaction instance with token parameters and optional keys.

        This transaction can be built in two ways to support flexibility:
        1) By passing a fully-formed TokenParams (and optionally TokenKeys) at construction time.
        2) By passing `None` and then using the various `set_*` methods.
            Validation is deferred until build time (`build_transaction_body()`), so you won't fail
            immediately if fields are missing at creation.

        Args:
        token_params (TokenParams, Optional): The token parameters (name, symbol, decimals, etc.).
                                    If None, a default/blank TokenParams is created,
                                    expecting you to call setters later.
        keys (TokenKeys, Optional): The token keys (admin, supply, freeze). If None, an empty TokenKeys
                                    is created, expecting you to call setter methods if needed.
        """
        super().__init__()

        # If user didn't provide token_params, assign simple default placeholders.
        if token_params is None:
            # It is expected the user will set valid values later.
            token_params = TokenParams(
                token_name="",
                token_symbol="",
                treasury_account_id=AccountId(0, 0, 1),
                decimals=0,
                initial_supply=0,
                token_type=TokenType.FUNGIBLE_COMMON,
                max_supply=0,
                supply_type=SupplyType.INFINITE,
                freeze_default=False
            )

        # Store TokenParams and TokenKeys.
        self._token_params: TokenParams = token_params
        self._keys: TokenKeys = keys if keys else TokenKeys()

        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def set_token_params(self, token_params: TokenParams) -> "TokenCreateTransaction":
        """
        Replaces the current TokenParams object with the new one.
        Useful if you have a fully-formed TokenParams to override existing fields.
        """
        self._require_not_frozen()
        self._token_params = token_params
        return self

    def set_token_keys(self, keys: TokenKeys) -> "TokenCreateTransaction":
        """
        Replaces the current TokenKeys object with the new one.
        Useful if you have a fully-formed TokenKeys to override existing fields.
        """
        self._require_not_frozen()
        self._keys = keys
        return self

    # These allow setting of individual fields
    def set_token_name(self, name: str) -> "TokenCreateTransaction":
        """ Sets the token name for the transaction."""
        self._require_not_frozen()
        self._token_params.token_name = name
        return self

    def set_token_symbol(self, symbol: str) -> "TokenCreateTransaction":
        """ Sets the token symbol for the transaction."""
        self._require_not_frozen()
        self._token_params.token_symbol = symbol
        return self

    def set_treasury_account_id(self, account_id: AccountId) -> "TokenCreateTransaction":
        """ Sets the treasury account ID for the token."""
        self._require_not_frozen()
        self._token_params.treasury_account_id = account_id
        return self
    
    def set_decimals(self, decimals: int) -> "TokenCreateTransaction":
        """ Sets the number of decimals for the token."""
        self._require_not_frozen()
        self._token_params.decimals = decimals
        return self

    def set_initial_supply(self, initial_supply: int) -> "TokenCreateTransaction":
        """ Sets the initial supply of the token."""
        self._require_not_frozen()
        self._token_params.initial_supply = initial_supply
        return self

    def set_token_type(self, token_type: TokenType) -> "TokenCreateTransaction":
        """ Sets the type of the token, such as fungible or non-fungible. """
        self._require_not_frozen()
        self._token_params.token_type = token_type
        return self
    
    def set_max_supply(self, max_supply: int) -> "TokenCreateTransaction":
        """ Sets the maximum supply of the token. For fungible tokens, this is the max number of tokens that can be created."""
        self._require_not_frozen()
        self._token_params.max_supply = max_supply
        return self

    def set_supply_type(self, supply_type: SupplyType) -> "TokenCreateTransaction":
        """ Sets the supply type of the token, such as finite or infinite."""
        self._require_not_frozen()
        self._token_params.supply_type = supply_type
        return self
    
    def set_freeze_default(self, freeze_default: bool) -> "TokenCreateTransaction":
        """ Sets the default freeze status for accounts associated with this token."""
        self._require_not_frozen()
        self._token_params.freeze_default = freeze_default
        return self

    def set_admin_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the admin key for the token, which allows updating and deleting the token."""
        self._require_not_frozen()
        self._keys.admin_key = key
        return self

    def set_supply_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the supply key for the token, which allows minting and burning tokens."""
        self._require_not_frozen()
        self._keys.supply_key = key
        return self

    def set_freeze_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the freeze key for the token, which allows freezing and unfreezing accounts."""
        self._require_not_frozen()
        self._keys.freeze_key = key
        return self
    
    def set_wipe_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the wipe key for the token, which allows wiping tokens from an account."""
        self._require_not_frozen()
        self._keys.wipe_key = key
        return self
    
    def set_metadata_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the metadata key for the token, which allows updating NFT metadata."""
        self._require_not_frozen()
        self._keys.metadata_key = key
        return self

    def set_pause_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the pause key for the token, which allows pausing and unpausing the token."""
        self._require_not_frozen()
        self._keys.pause_key = key
        return self
    
    def set_kyc_key(self, key: PrivateKey) -> "TokenCreateTransaction":
        """ Sets the KYC key for the token, which allows granting KYC to an account."""
        self._require_not_frozen()
        self._keys.kyc_key = key
        return self

    def _to_proto_key(self, private_key: Optional[PrivateKey]) -> Optional[basic_types_pb2.Key]:
        """
        Helper method to convert a private key to protobuf Key format.
        
        Args:
            private_key (PrivateKey, Optional): The private key to convert, or None
            
        Returns:
            basic_types_pb2.Key (Optional): The protobuf key or None if private_key is None
        """
        if not private_key:
            return None

        public_key_bytes = private_key.public_key().to_bytes_raw()
        return basic_types_pb2.Key(ed25519=public_key_bytes)

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token creation.

        Returns:
            transaction_body_pb2.TransactionBody: The protobuf transaction body containing the token creation details.

        Raises:
            ValueError: If required fields are missing or invalid.
        """

        # Validate all token params
        TokenCreateValidator._validate_token_params(self._token_params)

        # Validate freeze status
        TokenCreateValidator._validate_token_freeze_status(self._keys, self._token_params)
        
        admin_key_proto:    basic_types_pb2.Key = self._to_proto_key(self._keys.admin_key)
        supply_key_proto:   basic_types_pb2.Key = self._to_proto_key(self._keys.supply_key)
        freeze_key_proto:   basic_types_pb2.Key = self._to_proto_key(self._keys.freeze_key)
        wipe_key_proto:     basic_types_pb2.Key = self._to_proto_key(self._keys.wipe_key)
        metadata_key_proto: basic_types_pb2.Key = self._to_proto_key(self._keys.metadata_key)
        pause_key_proto:    basic_types_pb2.Key = self._to_proto_key(self._keys.pause_key)
        kyc_key_proto:      basic_types_pb2.Key = self._to_proto_key(self._keys.kyc_key)

        # Ensure token type is correctly set with default to fungible
        if self._token_params.token_type is None:
            token_type_value = 0  # default FUNGIBLE_COMMON
        elif isinstance(self._token_params.token_type, TokenType):
            token_type_value = self._token_params.token_type.value
        else:
            token_type_value = self._token_params.token_type

        # Ensure supply type is correctly set with default to infinite
        if self._token_params.supply_type is None:
            supply_type_value = 0  # default INFINITE
        elif isinstance(self._token_params.supply_type, SupplyType):
            supply_type_value = self._token_params.supply_type.value
        else:
            supply_type_value = self._token_params.supply_type

        # Construct the TokenCreateTransactionBody
        token_create_body = token_create_pb2.TokenCreateTransactionBody(
            name=self._token_params.token_name,
            symbol=self._token_params.token_symbol,
            decimals=self._token_params.decimals,
            initialSupply=self._token_params.initial_supply,
            tokenType=token_type_value,
            supplyType=supply_type_value,
            maxSupply=self._token_params.max_supply,
            freezeDefault=self._token_params.freeze_default,
            treasury=self._token_params.treasury_account_id._to_proto(),
            adminKey=admin_key_proto,
            supplyKey=supply_key_proto,
            freezeKey=freeze_key_proto,
            wipeKey=wipe_key_proto,
            metadata_key=metadata_key_proto,
            pause_key=pause_key_proto,
            kycKey=kyc_key_proto
        )
        # Build the base transaction body and attach the token creation details
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenCreation.CopyFrom(token_create_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.createToken,
            query_func=None
        )
