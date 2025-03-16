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

from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_create_pb2, basic_types_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

DEFAULT_TRANSACTION_FEE = 3_000_000_000


class TokenCreateValidator:
    """Token, key and freeze checks for creating a token as per the proto"""

    @staticmethod
    def validate_token_params(token_params):
        """
        Ensure valid values for the token characteristics.
        """
        required_fields = {
            "Token name": token_params.token_name,
            "Token symbol": token_params.token_symbol,
            "Treasury account ID": token_params.treasury_account_id,
        }

        # Ensure all required fields
        for field, value in required_fields.items():
            if not value:
                raise ValueError(f"{field} is required")

        # Ensure the token name and symbol are of valid byte length
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

        # Ensure initial supply is within max supply
        MAX_SUPPLY = 9_223_372_036_854_775_807  # 2^63 - 1

        if (
            not isinstance(token_params.initial_supply, int)
            or token_params.initial_supply < 0
        ):
            raise ValueError("Initial supply must be a non-negative integer")
        if token_params.initial_supply > MAX_SUPPLY:
            raise ValueError(f"Initial supply cannot exceed {MAX_SUPPLY}")

        # Ensure decimals are non-negative integers
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
    def validate_token_freeze_status(keys, token_params):
        """Ensure account is not frozen for this token."""
        if token_params.freeze_default:
            if not keys.freeze_key:
                # Without a freeze key but a frozen account, it is immutable.
                raise ValueError("Token is permanently frozen. Unable to proceed.")
            # With a freeze key but a frozen account, first unfreezing is required.
            raise ValueError(
                "Token frozen. Please complete a Token Unfreeze Transaction."
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
        freeze_default (optional): An initial Freeze status for accounts associated to this token.
    """

    token_name: str
    token_symbol: str
    treasury_account_id: AccountId
    decimals: int = 0  # Default to zero decimals
    initial_supply: int = 0  # Default to zero initial supply
    token_type: TokenType = TokenType.FUNGIBLE_COMMON  # Default to Fungible Common
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
    """

    admin_key: Optional[PrivateKey] = None
    supply_key: Optional[PrivateKey] = None
    freeze_key: Optional[PrivateKey] = None

class TokenCreateTransaction(Transaction):
    """
    Represents a token creation transaction on the Hedera network.

    This transaction creates a new token with specified properties, such as
    name, symbol, decimals, initial supply, and treasury account, leveraging the token and key params.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token creation transaction.
    """

    def __init__(self, token_params=None, keys=None):
        """
        Initializes a new TokenCreateTransaction instance with token parameters and optional keys.

        This transaction can be built in two ways to support flexibility:
        1) By passing a fully-formed TokenParams (and optionally TokenKeys) at construction time.
        2) By passing `None` (or partially filled objects) and then using the various `set_*` methods
            to set or override fields incrementally. Validation is deferred until build time (`build_transaction_body()`), so you won't fail
            immediately if fields are missing at creation.

        Args:
        token_params (TokenParams): The token parameters (name, symbol, decimals, etc.).
                                    If None, a default/blank TokenParams is created,
                                    expecting you to call setters later.
        keys (TokenKeys): The token keys (admin, supply, freeze). If None, an empty TokenKeys
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
                freeze_default=False
            )

        # Store TokenParams and TokenKeys.
        self._token_params = token_params
        self._keys = keys if keys else TokenKeys()

        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE
        self._is_frozen = False

    def set_token_params(self, token_params):
        """
        Replaces the current TokenParams object with the new one.
        Useful if you have a fully-formed TokenParams to override existing fields.
        """
        self._require_not_frozen()
        self._token_params = token_params
        return self

    def set_token_keys(self, keys):
        """
        Replaces the current TokenKeys object with the new one.
        Useful if you have a fully-formed TokenKeys to override existing fields.
        """
        self._require_not_frozen()
        self._keys = keys
        return self

    # These allow setting of individual fields
    def set_token_name(self, name):
        self._require_not_frozen()
        self._token_params.token_name = name
        return self

    def set_token_symbol(self, symbol):
        self._require_not_frozen()
        self._token_params.token_symbol = symbol
        return self

    def set_decimals(self, decimals):
        self._require_not_frozen()
        self._token_params.decimals = decimals
        return self

    def set_initial_supply(self, initial_supply):
        self._require_not_frozen()
        self._token_params.initial_supply = initial_supply
        return self

    def set_token_type(self, token_type):
        self._require_not_frozen()
        self._token_params.token_type = token_type
        return self

    def set_treasury_account_id(self, account_id):
        self._require_not_frozen()
        self._token_params.treasury_account_id = account_id
        return self

    def set_admin_key(self, key):
        self._require_not_frozen()
        self._keys.admin_key = key
        return self

    def set_supply_key(self, key):
        self._require_not_frozen()
        self._keys.supply_key = key
        return self

    def set_freeze_key(self, key):
        self._require_not_frozen()
        self._keys.freeze_key = key
        return self

    def freeze(self):
        """Marks the transaction as frozen to prevent further modifications."""
        self._is_frozen = True

    def _require_not_frozen(self):
        """
        Helper method ensuring no changes are made after freeze() has been called.
        """
        if self._is_frozen:
            raise ValueError("Transaction is frozen and cannot be modified.")

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the token creation details.

        Raises:
            ValueError: If required fields are missing or invalid.
        """

        # Validate all token params
        TokenCreateValidator.validate_token_params(self._token_params)

        # Validate freeze status
        TokenCreateValidator.validate_token_freeze_status(self._keys, self._token_params)

        admin_key_proto = None
        if self._keys.admin_key:
            admin_public_key_bytes = self._keys.admin_key.public_key().to_bytes_raw()
            admin_key_proto = basic_types_pb2.Key(ed25519=admin_public_key_bytes)

        supply_key_proto = None
        if self._keys.supply_key:
            supply_public_key_bytes = self._keys.supply_key.public_key().to_bytes_raw()
            supply_key_proto = basic_types_pb2.Key(ed25519=supply_public_key_bytes)

        freeze_key_proto = None
        if self._keys.freeze_key:
            freeze_public_key_bytes = self._keys.freeze_key.public_key().to_bytes_raw()
            freeze_key_proto = basic_types_pb2.Key(ed25519=freeze_public_key_bytes)


        # Ensure token type is correctly set with default to fungible
        if self._token_params.token_type is None:
            token_type_value = 0  # default FUNGIBLE_COMMON
        elif isinstance(self._token_params.token_type, TokenType):
            token_type_value = self._token_params.token_type.value
        else:
            token_type_value = self._token_params.token_type

        # Construct the TokenCreateTransactionBody
        token_create_body = token_create_pb2.TokenCreateTransactionBody(
            name=self._token_params.token_name,
            symbol=self._token_params.token_symbol,
            decimals=self._token_params.decimals,
            initialSupply=self._token_params.initial_supply,
            tokenType=token_type_value,
            treasury=self._token_params.treasury_account_id.to_proto(),
            adminKey=admin_key_proto,
            supplyKey=supply_key_proto,
            freezeKey=freeze_key_proto,
        )
        # Build the base transaction body and attach the token creation details
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenCreation.CopyFrom(token_create_body)

        return transaction_body

    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the token creation transaction using the provided client.

        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.

        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.

        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """
        response = client.token_stub.createToken(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")

        return self._get_receipt(client, response.transactionID)

    def _get_receipt(self, client, transaction_id):
        """
        Retrieves the transaction receipt.

        Args:
            client (Client): The client instance.
            transaction_id (TransactionID): The ID of the transaction.

        Returns:
            TransactionReceipt: The transaction receipt.

        Raises:
            Exception: If the receipt retrieval fails.
        """
        receipt = client.getTransactionReceipt(transaction_id)

        if receipt.status != 0:  # 0 means success
            raise Exception(receipt.status)

        return receipt

