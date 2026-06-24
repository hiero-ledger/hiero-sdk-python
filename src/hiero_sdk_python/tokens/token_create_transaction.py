"""
hiero_sdk_python.tokens.token_create_transaction.py.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Module for creating and validating Hedera token transactions.

This module includes:
- TokenParams: Represents token attributes.
- TokenKeys: Represents cryptographic keys for tokens.
- TokenCreateTransaction: Handles token creation transactions on Hedera.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, field

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import token_create_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.utils.key_utils import key_to_proto


AUTO_RENEW_PERIOD = Duration(7890000)  # around 90 days in seconds
DEFAULT_TRANSACTION_FEE = 3_000_000_000


@dataclass
class TokenParams:
    """
    Represents token attributes such as name, symbol, decimals, and type.

    Attributes:
        token_name (str, required): The name of the token.
        token_symbol (str, required): The symbol of the token.
        treasury_account_id (AccountId, required): The treasury account ID.
        decimals (int, optional): The number of decimals for the token. This must be zero for NFTs.
        initial_supply (int, optional): The initial supply of the token.
        token_type (TokenType, optional): The type of the token, defaulting to fungible.
        max_supply (int, optional): The max tokens or NFT serial numbers.
        supply_type (SupplyType, optional): The token supply status as finite or infinite.
        freeze_default (bool, optional): An initial Freeze status for accounts associated to this token.
        custom_fees (list[CustomFee], optional): The custom fees for the token.
        expiration_time (Timestamp, optional): The expiration time for token.
        auto_renew_account_id (AccountId, optional): The auto renew account id for the token.
        auto_renew_period (Duration, optional): The auto renew period for the token.
        memo (str, optional): The memo for the token.
        metadata (bytes, optional): The on-ledger token metadata as bytes (max 100 bytes).
    """

    token_name: str
    token_symbol: str
    treasury_account_id: AccountId
    decimals: int = 0  # Default to zero decimals
    initial_supply: int = 0  # Default to zero initial supply
    token_type: TokenType = TokenType.FUNGIBLE_COMMON  # Default to Fungible Common
    max_supply: int = 0  # Since defaulting to infinite
    supply_type: SupplyType = SupplyType.INFINITE  # Default to infinite
    freeze_default: bool = False
    custom_fees: list[CustomFee] = field(default_factory=list)
    expiration_time: Timestamp | None = None
    auto_renew_account_id: AccountId | None = None
    auto_renew_period: Duration | None = AUTO_RENEW_PERIOD  # Default around ~90 days
    memo: str | None = None
    metadata: bytes | None = None


@dataclass
class TokenKeys:
    """
    Represents cryptographic keys associated with a token.
    Does not include treasury_key which is for transaction signing.

    Attributes:
        admin_key (Key, optional): The admin key for the token to update and delete.
        supply_key (Key, optional): The supply key for the token to mint and burn.
        freeze_key (Key, optional): The freeze key for the token to freeze and unfreeze.
        wipe_key (Key, optional): The wipe key for the token to wipe tokens from an account.
        pause_key (Key, optional): The pause key for the token to be paused.
        metadata_key (Key, optional): The metadata key for the token to update NFT metadata.
        kyc_key (Key, optional): The KYC key for the token to grant KYC to an account.
        fee_schedule_key (Key, optional): The fee schedule key for the token.
    """

    admin_key: Key | None = None
    supply_key: Key | None = None
    freeze_key: Key | None = None
    wipe_key: Key | None = None
    metadata_key: Key | None = None
    pause_key: Key | None = None
    kyc_key: Key | None = None
    fee_schedule_key: Key | None = None


class TokenCreateTransaction(Transaction):
    """
    Represents a token creation transaction on the Hedera network.

    This transaction creates a new token with specified properties, such as
    name and symbol, leveraging the token and key params.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token creation transaction.
    """

    def __init__(self, token_params: TokenParams | None = None, keys: TokenKeys | None = None) -> None:
        """
        Initializes a new TokenCreateTransaction instance with token parameters and optional keys.

        This transaction can be built in two ways to support flexibility:
        1) By passing a fully-formed TokenParams (and optionally TokenKeys) at construction time.
        2) By passing `None` and then using the various `set_*` methods.
            Validation is deferred until build time (`build_transaction_body()`), so you won't fail
            immediately if fields are missing at creation.

        Args:
        token_params (TokenParams, optional): The token parameters (name, symbol, decimals, etc.).
                                    If None, a default/blank TokenParams is created,
                                    expecting you to call setters later.
        keys (TokenKeys, optional): The token keys (admin, supply, freeze).
                                    If None, an empty TokenKeys is created,
                                    expecting you to call setter methods if needed.
        """
        super().__init__()

        # If user didn't provide token_params, assign simple default placeholders.
        if token_params is None:
            # It is expected the user will set valid values later.
            token_params = TokenParams(
                token_name="",  # nosec B106
                token_symbol="",
                treasury_account_id=AccountId(0, 0, 1),
                decimals=0,
                initial_supply=0,
                token_type=TokenType.FUNGIBLE_COMMON,
                max_supply=0,
                supply_type=SupplyType.INFINITE,
                freeze_default=False,
                expiration_time=None,
                auto_renew_period=AUTO_RENEW_PERIOD,
            )

        # Store TokenParams and TokenKeys.
        self._token_params: TokenParams = token_params

        # Check if expiration time is set
        if token_params.expiration_time:
            self.set_expiration_time(token_params.expiration_time)

        # Check if auto_renew_period is set
        if token_params.auto_renew_period:
            self.set_auto_renew_period(token_params.auto_renew_period)

        self._keys: TokenKeys = keys if keys else TokenKeys()

        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def set_token_params(self, token_params: TokenParams) -> TokenCreateTransaction:
        """
        Replaces the current TokenParams object with the new one.
        Useful if you have a fully-formed TokenParams to override existing fields.
        """
        self._require_not_frozen()
        self._token_params = token_params
        return self

    def set_token_keys(self, keys: TokenKeys) -> TokenCreateTransaction:
        """
        Replaces the current TokenKeys object with the new one.
        Useful if you have a fully-formed TokenKeys to override existing fields.
        """
        self._require_not_frozen()
        self._keys = keys
        return self

    # These allow setting of individual fields
    def set_token_name(self, name: str) -> TokenCreateTransaction:
        """Sets the token name for the transaction."""
        self._require_not_frozen()
        self._token_params.token_name = name
        return self

    def set_token_symbol(self, symbol: str) -> TokenCreateTransaction:
        """Sets the token symbol for the transaction."""
        self._require_not_frozen()
        self._token_params.token_symbol = symbol
        return self

    def set_treasury_account_id(self, account_id: AccountId) -> TokenCreateTransaction:
        """Sets the treasury account ID for the token."""
        self._require_not_frozen()
        self._token_params.treasury_account_id = account_id
        return self

    def set_decimals(self, decimals: int) -> TokenCreateTransaction:
        """Sets the number of decimals for the token."""
        self._require_not_frozen()
        self._token_params.decimals = decimals
        return self

    def set_initial_supply(self, initial_supply: int) -> TokenCreateTransaction:
        """Sets the initial supply of the token."""
        self._require_not_frozen()
        self._token_params.initial_supply = initial_supply
        return self

    def set_token_type(self, token_type: TokenType) -> TokenCreateTransaction:
        """Sets the type of the token, such as fungible or non-fungible."""
        self._require_not_frozen()
        self._token_params.token_type = token_type
        return self

    def set_max_supply(self, max_supply: int) -> TokenCreateTransaction:
        """Sets the maximum supply of the token.
        For fungible tokens, this is the max number of tokens that can be created.
        """
        self._require_not_frozen()
        self._token_params.max_supply = max_supply
        return self

    def set_supply_type(self, supply_type: SupplyType) -> TokenCreateTransaction:
        """Sets the supply type of the token, such as finite or infinite."""
        self._require_not_frozen()
        self._token_params.supply_type = supply_type
        return self

    def set_freeze_default(self, freeze_default: bool) -> TokenCreateTransaction:
        """Sets the default freeze status for accounts associated with this token."""
        self._require_not_frozen()
        self._token_params.freeze_default = freeze_default
        return self

    def set_expiration_time(self, expiration_time: Timestamp) -> TokenCreateTransaction:
        """Sets the explicit expiration time for the token."""
        self._require_not_frozen()
        self._token_params.expiration_time = expiration_time
        # If expiration_time is set auto_renew_period will be effectively ignored
        self._token_params.auto_renew_period = None
        return self

    def set_auto_renew_period(self, auto_renew_period: Duration) -> TokenCreateTransaction:
        """Sets the auto-renew period for the token."""
        self._require_not_frozen()
        self._token_params.auto_renew_period = auto_renew_period
        return self

    def set_auto_renew_account_id(self, auto_renew_account_id: AccountId) -> TokenCreateTransaction:
        """Sets the auto-renew account ID for the token."""
        self._require_not_frozen()
        self._token_params.auto_renew_account_id = auto_renew_account_id
        return self

    def set_memo(self, memo: str) -> TokenCreateTransaction:
        """Sets a short description (memo) for the token."""
        self._require_not_frozen()
        self._token_params.memo = memo
        return self

    def set_admin_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the admin key for the token, which allows updating and deleting the token."""
        self._require_not_frozen()
        self._keys.admin_key = key
        return self

    def set_supply_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the supply key for the token, which allows minting and burning tokens."""
        self._require_not_frozen()
        self._keys.supply_key = key
        return self

    def set_freeze_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the freeze key for the token, which allows freezing and unfreezing accounts."""
        self._require_not_frozen()
        self._keys.freeze_key = key
        return self

    def set_wipe_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the wipe key for the token, which allows wiping tokens from an account."""
        self._require_not_frozen()
        self._keys.wipe_key = key
        return self

    def set_metadata_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the metadata key for the token, which allows updating NFT metadata."""
        self._require_not_frozen()
        self._keys.metadata_key = key
        return self

    def set_pause_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the pause key for the token, which allows pausing and unpausing the token."""
        self._require_not_frozen()
        self._keys.pause_key = key
        return self

    def set_kyc_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the KYC key for the token, which allows granting KYC to an account."""
        self._require_not_frozen()
        self._keys.kyc_key = key
        return self

    def set_custom_fees(self, custom_fees: list[CustomFee]) -> TokenCreateTransaction:
        """Set the Custom Fees."""
        self._require_not_frozen()
        self._token_params.custom_fees = custom_fees
        return self

    def set_fee_schedule_key(self, key: Key) -> TokenCreateTransaction:
        """Sets the fee schedule key for the token."""
        self._require_not_frozen()
        self._keys.fee_schedule_key = key
        return self

    def set_metadata(self, metadata: bytes | str) -> TokenCreateTransaction:
        """Sets the metadata for the token (max 100 bytes)."""
        self._require_not_frozen()

        # accept stringt and converts to bytes
        if isinstance(metadata, str):
            metadata = metadata.encode("utf-8")

        # type validation, if users pass something that is not a str or a byte
        if not isinstance(metadata, (bytes, bytearray)):
            raise TypeError("Metadata must be bytes or string")

        if len(metadata) > 100:
            raise ValueError("Metadata must not exceed 100 bytes")

        self._token_params.metadata = metadata
        return self

    def freeze_with(self, client) -> TokenCreateTransaction:
        """
        Freeze the transaction with the given client.

        This ensures that if an `auto_renew_period` is set but no `auto_renew_account_id`
        was provided by the user, the account ID is automatically assigned:
        - If `transaction_id` is already set → use its `account_id`.
        - Otherwise → fall back to the client's `operator_account_id`.

        """
        if self._token_params.auto_renew_account_id is None and self._token_params.auto_renew_period:
            self._token_params.auto_renew_account_id = (
                self.transaction_id.account_id if self.transaction_id else client.operator_account_id
            )

        return super().freeze_with(client)

    def _to_proto_key(self, key: Key | None):
        """
        Backwards-compatible wrapper around `key_to_proto` for converting SDK keys
        (PrivateKey or PublicKey) to protobuf `Key` messages.

        This exists so that existing unit tests and any external callers that rely
        on `_to_proto_key` continue to work after centralizing the logic in
        `hiero_sdk_python.utils.key_utils.key_to_proto`.
        """
        return key_to_proto(key)

    def _build_proto_body(self) -> token_create_pb2.TokenCreateTransactionBody:
        """
        Returns the protobuf body for the token create transaction.

        Returns:
            TokenCreateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Convert keys
        admin_key_proto = key_to_proto(self._keys.admin_key)
        supply_key_proto = key_to_proto(self._keys.supply_key)
        freeze_key_proto = key_to_proto(self._keys.freeze_key)
        wipe_key_proto = key_to_proto(self._keys.wipe_key)
        metadata_key_proto = key_to_proto(self._keys.metadata_key)
        pause_key_proto = key_to_proto(self._keys.pause_key)
        kyc_key_proto = key_to_proto(self._keys.kyc_key)
        fee_schedules_key_proto = key_to_proto(self._keys.fee_schedule_key)

        # Resolve enum values with defaults
        token_type_value = (
            self._token_params.token_type.value
            if isinstance(self._token_params.token_type, TokenType)
            else int(self._token_params.token_type or 0)
        )
        supply_type_value = (
            self._token_params.supply_type.value
            if isinstance(self._token_params.supply_type, SupplyType)
            else int(self._token_params.supply_type or 0)
        )

        # Construct the TokenCreateTransactionBody
        return token_create_pb2.TokenCreateTransactionBody(
            name=self._token_params.token_name,
            symbol=self._token_params.token_symbol,
            decimals=ctypes.c_uint32(self._token_params.decimals).value,
            initialSupply=ctypes.c_uint64(self._token_params.initial_supply).value,
            tokenType=token_type_value,
            supplyType=supply_type_value,
            maxSupply=self._token_params.max_supply,
            freezeDefault=self._token_params.freeze_default,
            treasury=self._token_params.treasury_account_id._to_proto(),
            expiry=(self._token_params.expiration_time._to_protobuf() if self._token_params.expiration_time else None),
            autoRenewAccount=(
                self._token_params.auto_renew_account_id._to_proto()
                if self._token_params.auto_renew_account_id
                else None
            ),
            autoRenewPeriod=(
                self._token_params.auto_renew_period._to_proto() if self._token_params.auto_renew_period else None
            ),
            memo=self._token_params.memo,
            metadata=self._token_params.metadata,
            adminKey=admin_key_proto,
            supplyKey=supply_key_proto,
            freezeKey=freeze_key_proto,
            wipeKey=wipe_key_proto,
            metadata_key=metadata_key_proto,
            pause_key=pause_key_proto,
            kycKey=kyc_key_proto,
            fee_schedule_key=fee_schedules_key_proto,
            custom_fees=[fee._to_proto() for fee in self._token_params.custom_fees],
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the token creation details.
        """
        token_create_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenCreation.CopyFrom(token_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenCreation.CopyFrom(token_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(transaction_func=channel.token.createToken, query_func=None)

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):  # noqa: PLR0912
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)
        if transaction_body.HasField("tokenCreation"):
            body = transaction_body.tokenCreation
            transaction._token_params.token_name = body.name
            transaction._token_params.token_symbol = body.symbol
            transaction._token_params.decimals = body.decimals
            transaction._token_params.initial_supply = body.initialSupply
            transaction._token_params.token_type = TokenType(body.tokenType)
            transaction._token_params.supply_type = SupplyType(body.supplyType)
            transaction._token_params.max_supply = body.maxSupply
            transaction._token_params.freeze_default = body.freezeDefault
            if body.HasField("treasury"):
                transaction._token_params.treasury_account_id = AccountId._from_proto(body.treasury)
            if body.HasField("expiry"):
                transaction._token_params.expiration_time = Timestamp._from_protobuf(body.expiry)
                transaction._token_params.auto_renew_period = None
            if body.HasField("autoRenewAccount"):
                transaction._token_params.auto_renew_account_id = AccountId._from_proto(body.autoRenewAccount)
            if body.HasField("autoRenewPeriod"):
                transaction._token_params.auto_renew_period = Duration._from_proto(body.autoRenewPeriod)
            transaction._token_params.memo = body.memo if body.memo else None
            transaction._token_params.metadata = body.metadata if body.metadata else None
            transaction._token_params.custom_fees = [CustomFee._from_proto(f) for f in body.custom_fees]
            if body.HasField("adminKey"):
                transaction._keys.admin_key = Key.from_proto_key(body.adminKey)
            if body.HasField("kycKey"):
                transaction._keys.kyc_key = Key.from_proto_key(body.kycKey)
            if body.HasField("freezeKey"):
                transaction._keys.freeze_key = Key.from_proto_key(body.freezeKey)
            if body.HasField("wipeKey"):
                transaction._keys.wipe_key = Key.from_proto_key(body.wipeKey)
            if body.HasField("supplyKey"):
                transaction._keys.supply_key = Key.from_proto_key(body.supplyKey)
            if body.HasField("fee_schedule_key"):
                transaction._keys.fee_schedule_key = Key.from_proto_key(body.fee_schedule_key)
            if body.HasField("pause_key"):
                transaction._keys.pause_key = Key.from_proto_key(body.pause_key)
            if body.HasField("metadata_key"):
                transaction._keys.metadata_key = Key.from_proto_key(body.metadata_key)
        return transaction
